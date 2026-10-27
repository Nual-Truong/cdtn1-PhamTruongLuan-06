# Nhật ký Gỡ lỗi (Bug Log) - Dự án Mekong Mobile ETL & Dashboard

Tài liệu ghi nhận các lỗi phát sinh trong quá trình tích hợp hệ thống Giai đoạn 2 theo quy trình 4 bước: Tái lập -> Khoanh vùng -> Sửa nguyên nhân -> Xác nhận.

---

## BUG-001 — Major — Lỗi cú pháp SQLite `unrecognized token: "{"` khi tải bảng cảnh báo doanh thu

| Dòng                      | Nội dung                                                                                                                                                                                                                                                           |
| :------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Mã và mức độ**       | BUG-001 — Major (Làm sập khung hiển thị cảnh báo doanh thu giảm 3 tháng liên tiếp trên Dashboard)                                                                                                                                                                  |
| **2. Phát hiện bởi**      | Kiểm thử tích hợp giao diện Dashboard (`streamlit run dashboard/app.py`) với bộ lọc Tỉnh/Thành phố                                                                                                                                                                 |
| **3. Triệu chứng**        | Giao diện báo lỗi `sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unrecognized token: "{"` tại câu truy vấn `WITH DoanhThuThang AS ...`                                                                                                               |
| **4. Cách tái lập**       | Mở Dashboard tại `http://localhost:8501`, chọn khoảng ngày bất kỳ từ `2024-01-01` đến `2026-12-31` có kèm biến điều kiện lọc tỉnh `{dk_tinh}`.                                                                                                                     |
| **5. Nguyên nhân**        | Chuỗi truy vấn đa dòng `sql_canh_bao` trong `dashboard/app.py` có chèn biến nội suy `{dk_tinh}` nhưng thiếu tiền tố `f` (f-string) ở đầu chuỗi `"""`. Python giữ nguyên cụm ký tự `{dk_tinh}` truyền thẳng xuống SQLite khiến trình phân tích cú pháp SQL báo lỗi. |
| **6. Cách sửa**           | Bổ sung tiền tố `f` trước chuỗi `sql_canh_bao = f"""..."""` trong `dashboard/app.py` và đồng bộ tên cột hiển thị trong hàm `highlight_max`.                                                                                                                        |
| **7. Commit và xác nhận** | Commit sửa lỗi trên nhánh `main` (tag `v0.2`) — Tải lại Dashboard ở cả trạng thái chọn "Tất cả" và chọn từng tỉnh cụ thể đều hiển thị bảng cảnh báo mượt mà, không còn lỗi.                                                                                        |

---

## BUG-002 — Major — Mất khách hàng trùng lặp khi thực hiện che số điện thoại (Data Masking) quá sớm

| Dòng                      | Nội dung                                                                                                                                                                                                                                                                             |
| :------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Mã và mức độ**       | BUG-002 — Major (Sai lệch số lượng khách hàng duy nhất trong bảng chiều `dim_customer` và vi phạm NFR03)                                                                                                                                                                             |
| **2. Phát hiện bởi**      | Kiểm thử đơn vị và đối chiếu số dòng sau pha Transform/Load (`pytest -q`)                                                                                                                                                                                                            |
| **3. Triệu chứng**        | Hai khách hàng khác nhau có cùng đầu số nhưng khác 4 số cuối (ví dụ `0901231111` và `0901232222`) bị gộp nhầm thành một bản ghi hoặc gây lỗi khi khử trùng lặp.                                                                                                                      |
| **4. Cách tái lập**       | Chạy hàm làm sạch khách hàng với bộ dữ liệu thử nghiệm chứa 2 số điện thoại trùng 6 số đầu và khác 4 số cuối, sau đó thực hiện deduplicate theo số điện thoại.                                                                                                                       |
| **5. Nguyên nhân**        | Nếu thực hiện che 4 số cuối (`090123****`) ngay ở pha Transform trước khi khử trùng (deduplicate) và tra cứu khóa (`customer_key`), các số điện thoại khác nhau sẽ biến thành chuỗi giống hệt nhau, làm hỏng khóa tự nhiên dùng để định danh khách hàng.                             |
| **6. Cách sửa**           | Giữ nguyên số điện thoại đã chuẩn hóa 10 số trong suốt pha Transform và Quality Check (CL1) để khử trùng và nối khóa chính xác; chỉ thực hiện cắt chuỗi che 4 số cuối (`sdt_masked`) ở bước cuối cùng ngay trước khi ghi vào bảng `dim_customer` trong `src/load/load_warehouse.py`. |
| **7. Commit và xác nhận** | Commit trên nhánh `main` (tag `v0.2`) — Chạy `pytest -q` PASS toàn bộ; kiểm tra bảng `dim_customer` đảm bảo 100% số điện thoại đều ở dạng `09xxxxxxxx` -> `09xxxx****` và giữ nguyên 55.385 khách hàng.                                                                              |

---

## BUG-003 — Minor — Lỗi lệch tên cột khi truy vấn bảng nhật ký lỗi `reject_rows` trên Dashboard

| Dòng                      | Nội dung                                                                                                                                                                                      |
| :------------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Mã và mức độ**       | BUG-003 — Minor (Khung số 5 hiển thị danh sách dòng bị từ chối trên Dashboard không tải được dữ liệu chi tiết)                                                                                |
| **2. Phát hiện bởi**      | Kiểm thử tích hợp US5 (Hiển thị bảng Reject Log và bộ lọc mã quy tắc CL1–CL5)                                                                                                                 |
| **3. Triệu chứng**        | Câu lệnh SQL lấy dữ liệu từ bảng `reject_rows` báo lỗi `no such column` đối với cột thời gian tạo hoặc nguồn dữ liệu.                                                                         |
| **4. Cách tái lập**       | Chạy `python -m src.pipeline` để nạp 634 dòng lỗi vào `reject_rows`, sau đó mở Dashboard kéo xuống Khung 5 (Bảng nhật ký dữ liệu bị từ chối).                                                 |
| **5. Nguyên nhân**        | Hợp đồng tên cột giữa kịch bản tạo bảng `sql/002_reject.sql` (`nguon`, `ma_quy_tac`, `ly_do`, `du_lieu_tho`, `ma_lo`, `tao_luc`) và câu lệnh `SELECT` trên `dashboard/app.py` chưa đồng nhất. |
| **6. Cách sửa**           | Đồng bộ lại câu truy vấn SQL trong `dashboard/app.py` khớp chính xác với tên cột vật lý trong `sql/002_reject.sql` và bổ sung `st.selectbox` cho phép lọc theo từng mã quy tắc.               |
| **7. Commit và xác nhận** | Commit trên nhánh `main` (tag `v0.2`) — Khung 5 hiển thị chính xác 634 dòng lỗi và lọc mượt mà theo từng mã quy tắc từ CL1 đến CL5.                                                           |
