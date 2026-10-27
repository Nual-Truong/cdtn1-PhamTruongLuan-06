# Báo cáo Thay đổi Thiết kế so với Bài tập 1 (Design Changes)

Trong quá trình hiện thực hóa hệ thống ETL Pipeline và Business Dashboard ở Giai đoạn 2 (Bài tập 2), kiến trúc tổng thể (3 pha ETL và mô hình kho dữ liệu Star Schema gồm 1 bảng Fact `fact_sales`, 4 bảng Dimension `dim_store`, `dim_product`, `dim_date`, `dim_customer` và bảng `reject_rows`) được **giữ nguyên theo đúng thiết kế ở Bài tập 1**.

Tuy nhiên, để đảm bảo tính tái lập (C5), bảo mật dữ liệu (NFR03) và trải nghiệm người dùng trên Dashboard, dự án đã thực hiện **3 tinh chỉnh kỹ thuật chi tiết** sau:

1. **Vị trí thực hiện che số điện thoại khách hàng (Data Masking - NFR03):**
   - **Thiết kế BT1:** Dự kiến che 4 số cuối số điện thoại ngay trong pha Transform (`clean_customers.py`).
   - **Hiện thực BT2:** Dời bước che 4 số cuối (`09xxxx****`) xuống cuối pha Load (`load_warehouse.py`) ngay trước khi ghi vào bảng `dim_customer`.
   - **Lý do:** Đảm bảo pha Transform và Quality Check (CL1) vẫn sử dụng được số điện thoại 10 số đầy đủ để khử trùng lặp khách hàng chính xác và ánh xạ đúng `customer_key` vào bảng `fact_sales`.

2. **Xử lý khóa ngoại mồ côi (Orphan Keys) bằng bản ghi `Unknown (-1)`:**
   - **Thiết kế BT1:** Loại bỏ các dòng giao dịch không tìm thấy mã khách hàng hoặc sản phẩm tương ứng.
   - **Hiện thực BT2:** Tạo các bản ghi mặc định có Surrogate Key = `-1` (`Unknown`) trong các bảng Dimension để ánh xạ cho các giao dịch thiếu thông tin chiều nhưng vẫn hợp lệ về mặt tài chính.
   - **Lý do:** Bảo toàn 100% tổng doanh thu thực tế của cửa hàng trong bảng `fact_sales`, tránh làm hụt số liệu tài chính khi lên báo cáo.

3. **Bổ sung bộ lọc tương tác cho bảng Nhật ký lỗi (`reject_rows` - US5) và đường tham chiếu trung bình (Mục D4):**
   - **Hiện thực BT2:** Bổ sung hộp chọn lọc theo từng mã quy tắc (`CL1` đến `CL5`) tại Khung 5 và thêm đường kẻ ngang tham chiếu mức doanh thu trung bình (Reference Line) trên biểu đồ cột nhằm đáp ứng tiêu chí trực quan hóa D4 của chuyên ngành DA.
