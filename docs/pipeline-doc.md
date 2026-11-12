# TÀI LIỆU PIPELINE ETL – MEKONG MOBILE

## 1. Mục đích

Pipeline ETL thực hiện trích xuất, làm sạch, kiểm định và nạp dữ liệu bán hàng Mekong Mobile vào Data Warehouse phục vụ phân tích.

Mã nguồn điều phối chính: `src/pipeline.py`.

## 2. Công nghệ và cấu hình

- Python.
- Pandas: xử lý dữ liệu dạng bảng.
- SQLAlchemy: kết nối và thao tác cơ sở dữ liệu.
- SQLite: cấu hình mặc định của Data Warehouse.
- Docker Compose: triển khai dịch vụ pipeline.
- CSV: định dạng dữ liệu nguồn.

Các biến môi trường:

| Biến | Ý nghĩa |
|---|---|
| DWH_URL | Chuỗi kết nối Data Warehouse |
| DATA_DIR | Thư mục chứa dữ liệu CSV |
| PSEUDO_KEY | Khóa bí mật dùng cho HMAC |
| APP_PORT | Cổng dịch vụ Docker |

Không ghi giá trị thực tế của PSEUDO_KEY vào tài liệu hoặc Git.

## 3. Cấu trúc mã nguồn

| Thành phần | Đường dẫn | Chức năng |
|---|---|---|
| Điều phối | src/pipeline.py | Điều phối toàn bộ ETL |
| Extract | src/extract/read_sources.py | Đọc các CSV nguồn |
| Transform | src/transform/clean_customers.py | Làm sạch khách hàng |
| Transform | src/transform/clean_orders.py | Làm sạch đơn hàng và chi tiết đơn |
| Quy tắc | src/transform/rules.py | Chuẩn hóa dữ liệu |
| Giả danh hóa | src/transform/gia_danh.py | Tạo HMAC-SHA256 |
| Quality | src/quality/checks.py | Kiểm tra CL1–CL5 |
| Quality | src/quality/three_dimensions.py | Đánh giá chất lượng ba chiều |
| Load staging | src/load/load_staging.py | Ghi staging, reject và báo cáo |
| Load DWH | src/load/load_warehouse.py | Tạo dimension và fact |
| Logging | src/log_config.py | Định dạng log JSON |

## 4. Dữ liệu đầu vào

Pipeline đọc năm tệp CSV:

- customers_raw.csv
- orders_2024_2026.csv
- order_items.csv
- products.csv
- stores.csv

Thư mục mặc định là `dataset/`, có thể thay đổi bằng biến DATA_DIR.

Nếu dữ liệu khách hàng hoặc đơn hàng rỗng, pipeline ghi lỗi và dừng xử lý.

## 5. Quy trình ETL

### 5.1. Khởi tạo cơ sở dữ liệu

Pipeline đọc các tệp SQL trong thư mục `sql/` theo thứ tự tên tệp để khởi tạo cấu trúc.

Lưu ý: phần khởi tạo hiện bỏ qua ngoại lệ khi thực thi từng câu SQL. Vì vậy cần kiểm tra schema thực tế sau khi khởi tạo, không mặc định mọi câu SQL đều thành công.

### 5.2. Extract

Đọc dữ liệu khách hàng, đơn hàng, chi tiết đơn hàng, sản phẩm và cửa hàng từ CSV.

### 5.3. Transform

Thực hiện làm sạch khách hàng và đơn hàng, xử lý dữ liệu không hợp lệ và tạo tập dữ liệu reject.

Có thể lọc dữ liệu đơn hàng theo khoảng ngày bằng hai tham số:

- `--tu-ngay`
- `--den-ngay`

### 5.4. Data Quality

Pipeline thực hiện các kiểm định CL1–CL5 trên dữ liệu thô:

- CL1: kiểm tra số điện thoại hợp lệ.
- CL2: kiểm tra ngày hợp lệ.
- CL3: kiểm tra tính khớp của giá trị tiền.
- CL4: kiểm tra khóa không trùng.
- CL5: kiểm tra khóa ngoại tồn tại.

Ngoài ra, pipeline đo ba chiều chất lượng dữ liệu: đầy đủ, chính xác và nhất quán.

Kết quả được ghi vào báo cáo chất lượng.

### 5.5. Load Staging và Reject

Staging sử dụng allowlist để giới hạn cột được ghi:

- staging_customers: record_id, ngay_tao, sdt_che, khoa_khach_hang, batch_id.
- staging_orders: order_id, ma_don, ma_cua_hang, ngay_chuan, thanh_tien, khoa_khach_hang, batch_id.

Reject lưu metadata phục vụ truy vết. Trường du_lieu_goc được kiểm tra JSON và chỉ chấp nhận hai khóa `nguon`, `ma_ban_ghi`.

### 5.6. Load Data Warehouse

Hàm `nap_kho_du_lieu()` tạo và nạp các bảng:

- dim_store
- dim_product
- dim_date
- dim_customer
- fact_sales

Các dimension có bản ghi UNKNOWN với khóa -1 để xử lý trường hợp không xác định.

Fact_sales tổng hợp theo order_key, product_key, date_key, store_key và customer_key.

## 6. Batch và báo cáo

Mã batch mặc định: `lo-toan-bo`.

Khi có tham số ngày, mã batch được tạo theo dạng:

`lo-YYYY-MM-DD-YYYY-MM-DD`

Pipeline tạo báo cáo JSON tại `reports/` và báo cáo chất lượng Markdown tại `reports/chat-luong.md`.

Log chạy pipeline được lưu theo dạng `reports/run_<batch_id>.log`.

## 7. Triển khai Docker

Docker Compose khai báo service `pipeline`.

- Container: mekong_da_pipeline.
- Cổng mặc định: 8501.
- Volume dữ liệu: dwh_data ánh xạ vào `/app/data`.
- Volume báo cáo: `./reports` ánh xạ vào `/app/reports`.
- Healthcheck kiểm tra endpoint Streamlit `/_stcore/health`.

PSEUDO_KEY là biến môi trường bắt buộc khi khởi động Compose.

## 8. Giới hạn kỹ thuật cần lưu ý

1. Hàm ghi staging và reject đang dùng `if_exists="replace"`. Mỗi lần ghi có thể thay thế nội dung bảng hiện tại, do đó chưa thể khẳng định dữ liệu lịch sử của nhiều batch được giữ lại.
2. Phần khởi tạo SQL bỏ qua ngoại lệ thực thi. Cần kiểm tra schema runtime.
3. Việc chạy lại cùng khoảng ngày chưa đủ để kết luận toàn bộ pipeline có tính idempotent.
4. `src/log_config.py` định nghĩa formatter JSON, nhưng pipeline hiện cấu hình logging riêng bằng `logging.basicConfig`; không nên khẳng định toàn bộ log pipeline đều ở định dạng JSON.
5. Cần đối chiếu schema thực tế trong SQLite với các câu lệnh SQL thiết kế vì một số tên cột và cấu trúc có thể khác nhau.

## 9. Kiểm thử

Kết quả kiểm thử đã thực hiện trong Docker:

- 12/12 test PASS.
- Bộ test nằm trong `tests/test_rules.py` và `tests/test_checks.py`.

Kết quả này phản ánh lần chạy kiểm thử đã ghi nhận, không thay thế việc kiểm thử lại sau các thay đổi mã nguồn.
