# KẾ HOẠCH KIỂM THỬ (TEST PLAN) – SMART CRM MEKONG MOBILE

**Luồng nghiệp vụ:** Luồng L6 – Xây dựng Kho dữ liệu và Báo cáo BI phân tích bán hàng  
**Chuyên ngành (Track):** Data Analytics (DA)  
**Phiên bản:** v1.0 (Bài tập 3)

---

## 1. Phạm vi kiểm thử (Scope)

### 1.1. Phần thực hiện kiểm thử (In-Scope)

- **Tầng Transform & Chuẩn hóa dữ liệu (`src/transform/`):**
  - Kiểm thử hàm chuẩn hóa số điện thoại `chuan_hoa_dien_thoai` với các định dạng hợp lệ (10 chữ số, dấu chấm, khoảng trắng, mã vùng `+84`), giá trị biên độ dài (9, 10, 11 số) và dữ liệu rác/rỗng.
  - Kiểm thử hàm đọc ngày giao dịch `doc_ngay` theo 3 khuôn định dạng (`%d/%m/%Y`, `%d-%m-%y`, `%Y.%m.%d`) và từ chối ngày sai quy cách.
  - Kiểm thử hàm chuẩn hóa họ tên tiếng Việt `chuan_hoa_ten` (bao gồm ký tự `Đ/đ`) và tạo khóa hợp nhất khách hàng `khoa_hop_nhat`.
- **Tầng Kiểm định chất lượng dữ liệu & Hợp đồng dữ liệu (`src/quality/`, `src/transform/`):**
  - Kiểm thử 5 quy tắc chất lượng cốt lõi: `CL1` (SĐT chuẩn hóa được), `CL2` (Ngày giao dịch hợp lệ), `CL3` (`thanh_tien = so_luong * don_gia` với sai số làm tròn $\le 1$ đồng), `CL4` (Cặp khóa `(ma_cua_hang, ma_don)` duy nhất), `CL5` (Toàn vẹn tham chiếu `order_items.order_id` tồn tại trong `orders`).
  - Kiểm thử cơ chế tách toàn bộ dòng vi phạm (`CL1`–`CL5`) vào bảng `reject_rows` kèm mã quy tắc, lý do lỗi tiếng Việt và dữ liệu gốc JSON (`du_lieu_goc`).
  - Kiểm thử bộ đo **Ba chiều chất lượng dữ liệu Track DA** (`ĐẦY ĐỦ` theo từng cột, `CHÍNH XÁC` theo quy tắc nghiệp vụ, `NHẤT QUÁN` giữa các bảng) và sinh báo cáo tự động.
- **Tầng Load, Bảo mật & Tích hợp Pipeline (`src/load/`, `src/pipeline.py`):**
  - Kiểm thử quy tắc bảo mật Data Masking (`NFR03`): che 4 số cuối số điện thoại khách hàng (`090123****`) và đảm bảo không lộ thông tin nhạy cảm.
  - Kiểm thử tính tái lập (Idempotency): chạy lại toàn bộ ETL Pipeline lần thứ hai trên cùng lô dữ liệu không gây lỗi và không làm nhân đôi bản ghi tại các bảng `dim_store`, `dim_product`, `dim_date`, `dim_customer`, `fact_sales`.

### 1.2. Phần CHỦ Ý KHÔNG kiểm thử (Out-of-Scope) và Lý do

- **Không kiểm thử hiệu năng chịu tải lớn (Load / Stress Testing) và luồng Streaming thời gian thực:** Hệ thống hiện tại xử lý theo lô (Batch ETL) trên quy mô ~128.000 dòng dữ liệu; bài toán tối ưu tải lớn và Real-time streaming thuộc phạm vi mở rộng của Chuyên đề tốt nghiệp 2.
- **Không viết kiểm thử tự động giao diện (UI End-to-End Testing) cho biểu đồ Streamlit Dashboard:** Tuân thủ nguyên tắc Kim tự tháp kiểm thử (tránh mô hình "hình nón ngược" chậm và dễ vỡ khi thay đổi nhãn giao diện); 3 trạng thái giao diện (Đang tải, Rỗng, Lỗi kết nối) đã được kiểm chứng trực quan ở Bài tập 2.

---

## 2. Loại kiểm thử, Số lượng theo tầng và Kỹ thuật chọn dữ liệu

### 2.1. Phân bổ theo Kim tự tháp kiểm thử (Tổng số: 12 Test Cases)

- **Tầng Unit Test (7 test cases: `TC-01` đến `TC-07`):** Kiểm thử cô lập các hàm xử lý nghiệp vụ thuần trong `src/transform/rules.py` và `src/quality/checks.py`, không phụ thuộc CSDL, thời gian chạy dưới 1 giây.
- **Tầng Integration Test (3 test cases: `TC-08` đến `TC-10`):** Kiểm thử sự phối hợp giữa tầng làm sạch (`clean_customers.py`, `clean_orders.py`), kiểm định chất lượng và tách dòng lỗi vào `df_reject`.
- **Tầng System / Pipeline Test (2 test cases: `TC-11`, `TC-12`):** Kiểm thử tích hợp toàn luồng ETL Pipeline (`src/pipeline.py`) với CSDL SQLite, báo cáo chất lượng 3 chiều và Kho dữ liệu Star Schema.

### 2.2. Độ phủ 5 loại kiểm thử bắt buộc của Bài tập 3

1. **Luồng đúng (Positive Testing – 3 TC):** `TC-01` (Chuẩn hóa 4 định dạng SĐT), `TC-02` (Đọc 3 khuôn ngày chuẩn), `TC-08` (Hợp đồng làm sạch khách hàng & đơn hàng hợp lệ).
2. **Giá trị biên (Boundary Value Testing – 3 TC, đặt ở hai bên ranh giới):**
   - `TC-03`: Biên độ dài số điện thoại tại ranh giới 10 chữ số (`9` chữ số -> Từ chối; `10` chữ số -> Hợp lệ; `11` chữ số -> Từ chối).
   - `TC-04`: Biên sai số thành tiền `CL3` ngay tại ngưỡng cho phép $\le 1$ đồng (`thanh_tien` lệch `1` đồng -> Hợp lệ).
   - `TC-05`: Biên sai số thành tiền `CL3` sát ngoài ngưỡng cho phép (`thanh_tien` lệch `2` đồng -> Bị bắt lỗi `CL3` và đẩy vào `reject_rows`).
3. **Dữ liệu sai (Negative Testing – 3 TC):** `TC-06` (Đầu vào SĐT/ngày là `None`, rỗng, khoảng trắng, chuỗi chữ `'abc'`), `TC-09` (Đơn hàng sai ngày `CL2` và trùng cặp khóa `(ma_cua_hang, ma_don)` `CL4`), `TC-10` (Chi tiết đơn hàng mồ côi không khớp `order_id` `CL5` bị đẩy vào `reject_rows`).
4. **Bảo mật / Chất lượng dữ liệu (Security & Data Quality Testing – 2 TC):** `TC-07` (Chuẩn hóa tên tiếng Việt chứa chữ `Đ/đ` để chống sai lệch khóa định danh khách hàng & kiểm tra che SĐT `NFR03`), `TC-11` (Đo chất lượng dữ liệu trên dữ liệu gốc trước khi lọc và phát hiện vi phạm ngưỡng chất lượng).
5. **Tính tái lập (Reproducibility Testing – 1 TC):** `TC-12` (Chạy ETL Pipeline 2 lần liên tiếp trên cùng lô dữ liệu, số dòng trong `fact_sales` và các bảng `dim_*` giữ nguyên 100%, không nhân đôi).

### 2.3. Kỹ thuật chọn dữ liệu thử

- **Phân vùng tương đương (Equivalence Partitioning):** Chia đầu vào thành miền hợp lệ (SĐT 10 số/mã `+84`, ngày thuộc 3 khuôn chuẩn, đơn hàng khớp thành tiền & khóa ngoại) và miền không hợp lệ (chuỗi ký tự chữ, chuỗi rỗng, `None`, ngày sai lịch, đơn hàng trùng khóa hoặc mồ côi).
- **Phân tích giá trị biên (Boundary Value Analysis):** Đặt dữ liệu thử ngay tại ranh giới và sát hai bên ranh giới cho độ dài chuỗi SĐT (`9`, `10`, `11` ký tự số) và độ lệch công thức `abs(thanh_tien - so_luong * don_gia) <= 1` (`0`, `1`, `2` đồng) để bắt lỗi so sánh `<` và `<=`.

---

## 3. Tiêu chí thành công đo được (Measurable Success Criteria)

- **Độ phủ thực thi:** Đạt **12/12 test cases** được chạy thực tế, ghi nhận kết quả cụ thể vào bảng 8 cột trong `docs/test-report.md` kèm ảnh chụp màn hình trong `docs/screenshots/TC-01.png` ... `TC-12.png`.
- **Độ phủ nghiệp vụ:** **100% quy tắc nghiệp vụ** (`CL1`–`CL5`, chuẩn hóa tên/SĐT, Data Masking `NFR03`, Idempotency) và **3 chiều chất lượng dữ liệu** (`ĐẦY ĐỦ`, `CHÍNH XÁC`, `NHẤT QUÁN`) có ít nhất 1 test case kiểm chứng.
- **Xử lý lỗi & Hồi quy:** Mọi bug phát hiện trong quá trình chạy test (tối thiểu $\ge 3$ bug, có $\ge 1$ bug mức `Critical` hoặc `Major`) đều được điều tra nguyên nhân gốc, ghi vào `docs/bug-log.md` đủ 7 dòng, sửa triệt để với commit riêng và chạy lại đạt **100% PASS** bằng một lệnh `pytest -v`.

---

## 4. Môi trường và Dữ liệu thử (Environment & Test Data)

- **Môi trường kiểm thử:**
  - Hệ điều hành: Windows 10/11 (PowerShell) và Ubuntu Latest (trên GitHub Actions CI).
  - Runtime & Thư viện: Python 3.11+, `pytest`, `pandas`, `sqlalchemy`, `sqlite3` (cài đặt từ `requirements.txt`).
- **Chiến lược dựng dữ liệu thử (Test Fixtures):**
  - Các test case `TC-01` đến `TC-11` tự khởi tạo DataFrame và CSDL SQLite cô lập (`tmp_path` / in-memory) ngay trong code kiểm thử, tuyệt đối không phụ thuộc trạng thái dữ liệu sẵn có trên máy cá nhân.
  - Test case tích hợp `TC-12` kiểm thử trên cấu trúc SQL chuẩn (`sql/001_staging.sql` -> `sql/020_fact.sql`) và tập dữ liệu mẫu.
- **Lệnh thực thi chuẩn:**
  - Chạy toàn bộ bộ kiểm thử tự động: `pytest -v` (hoặc `pytest -q`).
  - Chạy luồng ETL Pipeline: `python -m src.pipeline`.

## 5.
