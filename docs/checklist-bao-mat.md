# CHECKLIST BẢO MẬT – MEKONG MOBILE ETL

## 1. Mục đích

Tài liệu tổng hợp các biện pháp bảo vệ dữ liệu đã được triển khai và các kết quả kiểm tra trong project.

Trạng thái được phân biệt:
- Đã kiểm tra: có kết quả kiểm thử hoặc đối chiếu trực tiếp.
- Có trong mã nguồn: đã tìm thấy cơ chế trong code.
- Chưa xác minh: chưa đủ bằng chứng để kết luận hoạt động đầy đủ.

## 2. Quản lý bí mật

| Nội dung | Trạng thái | Bằng chứng |
|---|---|---|
| Không đưa .env vào Git | Đã kiểm tra | git ls-files và git check-ignore |
| .env được Git ignore | Đã kiểm tra | Quy tắc .gitignore dòng 5 |
| PSEUDO_KEY bắt buộc | Có trong mã nguồn | docker-compose.yml |
| Kiểm tra khóa tối thiểu 32 byte | Đã kiểm tra | src/transform/gia_danh.py |
| Không in giá trị khóa trong báo cáo | Đã thực hiện | Quy trình kiểm thử không hiển thị khóa |

Không lưu khóa bí mật trực tiếp trong mã nguồn, tài liệu, ảnh minh chứng hoặc repository.

## 3. Giả danh hóa dữ liệu

| Nội dung | Trạng thái |
|---|---|
| Sử dụng HMAC-SHA256 | Đã kiểm tra |
| Khóa có tối thiểu 32 byte | PASS |
| Kết quả có 64 ký tự hexadecimal | PASS |
| Cùng đầu vào tạo cùng kết quả | PASS |
| Đầu vào khác tạo kết quả khác | PASS |

Hàm `gia_danh()` trong `src/transform/gia_danh.py` sử dụng HMAC-SHA256 với khóa PSEUDO_KEY.

HMAC là cơ chế tạo mã xác thực một chiều có khóa, không phải mã hóa hai chiều. Không thể dùng kết quả HMAC để khôi phục trực tiếp dữ liệu ban đầu.

## 4. Giới hạn dữ liệu Staging

`src/load/load_staging.py` định nghĩa allowlist cho hai bảng staging.

### staging_customers

Các trường được phép:
- record_id
- ngay_tao
- sdt_che
- khoa_khach_hang
- batch_id

### staging_orders

Các trường được phép:
- order_id
- ma_don
- ma_cua_hang
- ngay_chuan
- thanh_tien
- khoa_khach_hang
- batch_id

Hàm `ghi_lo()` chỉ chọn các cột trong allowlist trước khi ghi dữ liệu.

## 5. Kiểm soát Reject

Hàm `kiem_tra_json_reject()` kiểm tra:
- Giá trị JSON không được để trống.
- JSON phải hợp lệ.
- Dữ liệu phải có kiểu object.
- Chỉ chấp nhận khóa `nguon` và `ma_ban_ghi`.

Các trường khác bị từ chối.

Đây là biện pháp giới hạn nội dung JSON Reject, không phải bằng chứng rằng toàn bộ hệ thống không thể phát sinh PII ở các vị trí khác.

## 6. Log và dữ liệu nhạy cảm

Đã kiểm tra file `reports/run_lo-toan-bo.log`:

| Nội dung kiểm tra | Kết quả |
|---|---|
| Giá trị PSEUDO_KEY xuất hiện trong log | Không phát hiện |
| Mẫu email | 0 kết quả |
| Mẫu số điện thoại | 0 kết quả |

Kết luận: không phát hiện các mẫu nhạy cảm đã kiểm tra trong file log tại thời điểm thực hiện.

Giới hạn: đây là rà soát theo mẫu regex, không phải kiểm toán toàn diện. Không thể kết luận log không chứa mọi loại thông tin cá nhân.

Mã nguồn `src/log_config.py` có định nghĩa formatter JSON. Tuy nhiên, pipeline hiện sử dụng cấu hình logging riêng trong `src/pipeline.py`. Không khẳng định toàn bộ log đang được ghi theo JSON.

## 7. Kiểm soát triển khai

| Nội dung | Trạng thái |
|---|---|
| PSEUDO_KEY được yêu cầu trong Docker Compose | Có trong cấu hình |
| Dữ liệu DWH được gắn volume | Có trong cấu hình |
| Reports được gắn volume | Có trong cấu hình |
| Healthcheck container | Có trong cấu hình |
| Kiểm soát truy cập theo vai trò RBAC | Chưa xác minh |
| Row-Level Security (RLS) | Chưa xác minh |
| Mã hóa dữ liệu lưu trữ | Chưa xác minh |
| Mã hóa kết nối mạng | Chưa xác minh |

Việc có file SQL về quyền truy cập không đồng nghĩa RBAC hoặc RLS đã hoạt động trên SQLite.

## 8. Kiểm thử liên quan

Các kiểm thử đã ghi nhận:

- 12/12 test PASS trong Docker.
- Kiểm tra HMAC-SHA256 đạt.
- Kiểm tra Git ignore của .env đạt.
- Rà soát log không phát hiện các mẫu email, số điện thoại và giá trị PSEUDO_KEY.

Các kết quả trên phản ánh phạm vi kiểm tra đã thực hiện, không phải chứng nhận an toàn tuyệt đối.

## 9. Hạn chế và hướng cải thiện

1. Xem xét thay `if_exists="replace"` bằng cơ chế nạp dữ liệu có kiểm soát để tránh mất dữ liệu batch trước.
2. Không bỏ qua âm thầm ngoại lệ khi thực thi SQL; cần ghi log và dừng khi lỗi cấu trúc quan trọng.
3. Bổ sung kiểm tra PII toàn diện hơn cho log, staging, reject và báo cáo.
4. Xác minh cơ chế phân quyền phù hợp với hệ quản trị cơ sở dữ liệu triển khai.
5. Xem xét mã hóa dữ liệu lưu trữ, sao lưu và quản lý vòng đời khóa.
6. Rà soát dependency và cập nhật phiên bản an toàn định kỳ.

## 10. Kết luận

Project đã triển khai một số biện pháp bảo vệ dữ liệu gồm quản lý khóa qua biến môi trường, HMAC-SHA256, allowlist staging và kiểm soát JSON Reject.

Các kiểm tra hiện tại đạt kết quả trong phạm vi đã thực hiện. Những nội dung chưa có bằng chứng triển khai cần được ghi nhận là giới hạn, không trình bày như chức năng đã hoàn thành.
