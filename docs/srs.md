# BẢN ĐẶC TẢ YÊU CẦU PHẦN MỀM (SRS) - RÚT GỌN
**Học phần:** Chuyên đề tốt nghiệp 1
**Dự án:** Smart CRM - Mekong Mobile 
**Track:** Data Analytics (DA) - Luồng phân tích dữ liệu bán hàng
**Sinh viên thực hiện:** Phạm Trường Luân (MSSV: 2374802010296)

---

## 1. Giới thiệu và phạm vi
- **Bối cảnh:** Mekong Mobile là chuỗi bán lẻ thiết bị di động với 24 cửa hàng. Hiện tại, dữ liệu bán hàng đang bị phân mảnh ở nhiều file CSV, khiến Ban Giám đốc gặp khó khăn trong việc theo dõi doanh thu tổng thể và đánh giá độ trung thành của khách hàng.
- **Luồng nghiệp vụ lựa chọn:** Xây dựng Kho dữ liệu (Data Warehouse) bán hàng và thiết kế Dashboard phân tích doanh thu, tập trung vào việc tính toán tổng doanh thu, cảnh báo suy giảm và phân tích tỉ lệ khách quay lại (Retention).
- **Ngoài phạm vi (WON'T):** 
  * Dự báo doanh thu bằng mô hình AI.
  * Cập nhật dữ liệu theo thời gian thực (Real-time streaming).
- **Bảng thuật ngữ:**
  * **Cửa hàng:** Chi nhánh bán lẻ vật lý của Mekong Mobile.
  * **Sản phẩm:** Điện thoại, máy tính bảng hoặc phụ kiện bán tại cửa hàng.
  * **Thành tiền:** Doanh thu thực tế của một dòng sản phẩm trong đơn hàng (đã trừ khuyến mãi nếu có).
  * **Khách hàng:** Người mua hàng, được định danh duy nhất thông qua số điện thoại.

## 2. Các bên liên quan và vai trò
- **Giám đốc:** Người dùng cuối (End-user) quan trọng nhất. Sử dụng Dashboard để xem tổng doanh thu, theo dõi tình hình kinh doanh của các cửa hàng và xem các cảnh báo giảm doanh thu. Không có quyền can thiệp vào quy trình nạp dữ liệu.
- **Trưởng phòng Marketing:** Người dùng khai thác dữ liệu để phân tích độ trung thành của khách hàng (Retention) và hiệu quả của các nhóm sản phẩm. 
- **Data Engineer:** Quản trị viên hệ thống. Chịu trách nhiệm thiết kế luồng ETL, theo dõi quá trình nạp dữ liệu (batch) hàng ngày và xử lý các dòng dữ liệu bị loại (reject log).

## 3. Yêu cầu chức năng (FR) & User Story
- **FR01:** Hệ thống phải cung cấp báo cáo tổng doanh thu theo từng cửa hàng lọc theo tháng/năm.
- **FR02:** Hệ thống phải tự động highlight cảnh báo các cửa hàng có doanh thu giảm liên tiếp trong 3 tháng.
- **FR03:** Hệ thống phải tính toán và hiển thị tỉ lệ phần trăm khách hàng mua từ 2 đơn hàng trở lên (Retention rate).
- **FR04:** Hệ thống phải cho phép phân tích doanh thu chi tiết theo từng nhóm sản phẩm.
- **FR05:** Hệ thống phải ghi nhận và báo cáo các dòng dữ liệu bị lỗi định dạng trong quá trình ETL (reject log).

**Danh sách User Story (Đã chuẩn hóa):**
- **US1 (MUST):** Là Giám đốc, tôi muốn xem tổng doanh thu từng cửa hàng theo tháng/năm và lọc theo tỉnh/thành phố để đánh giá hiệu quả kinh doanh.
- **US2 (MUST):** Là Giám đốc, tôi muốn xác định các cửa hàng có doanh thu giảm 3 tháng liên tiếp để có biện pháp xử lý kịp thời.
- **US3 (MUST):** Là Quản trị viên, tôi muốn chuẩn hóa và che giấu 4 số cuối điện thoại khách hàng (Data Masking) để bảo vệ quyền riêng tư cá nhân.
- **US4 (SHOULD):** Là Trưởng phòng Marketing, tôi muốn tính tỉ lệ khách quay lại mua lần hai (Retention) để đánh giá mức độ trung thành.
- **US5 (SHOULD):** Là Data Engineer, tôi muốn tách các dòng dữ liệu bị lỗi định dạng vào bảng Reject Log để không làm sai lệch số liệu tài chính.
- **US6 (COULD):** Là Data Engineer, tôi muốn xem và lọc danh sách chi tiết các dòng lỗi theo từng mã quy tắc (`CL1` đến `CL5`) ngay trên Dashboard.
- **US7 (COULD):** Là Data Engineer, tôi muốn luồng ETL có tính tái lập (Idempotency) để chạy lại nhiều lần không bị nhân đôi dữ liệu.

## 4. Yêu cầu phi chức năng (NFR)
- **NFR01 (Hiệu năng):** Với khối lượng 100.000 dòng dữ liệu trong kho, Dashboard báo cáo phải tải xong và hiển thị hoàn chỉnh trong dưới **3 giây**.
- **NFR02 (Sẵn sàng/Bảo trì):** Quá trình ETL nạp dữ liệu từ các file CSV vào Kho dữ liệu (chạy batch ban đêm) phải hoàn thành trong thời gian tối đa là **2 giờ** đồng hồ.
- **NFR03 (Bảo mật):** Nhằm bảo mật thông tin, hệ thống tự động che giấu **4 số cuối** điện thoại của khách hàng (Data Masking) ngay tại tầng ETL trước khi nạp vào kho dữ liệu. *(Ví dụ: Số điện thoại gốc `0901234567` sẽ được biến đổi thành `090123****`)*.

## 5. Ràng buộc và quy tắc nghiệp vụ
- **QT-01:** Một đơn hàng hợp lệ được ghi nhận doanh thu bắt buộc phải có đầy đủ mã cửa hàng, mã sản phẩm và ngày giao dịch.
- **QT-02:** Doanh thu của sản phẩm (thành tiền) được tính bằng `so_luong` nhân với `don_gia` tại thời điểm bán.
- **QT-03:** Các dòng dữ liệu bị lỗi định dạng trong file CSV nguồn sẽ bị đẩy vào `reject_log` thay vì làm sập toàn bộ tiến trình nạp (ETL).

## 6. Bảng truy vết yêu cầu (Traceability Matrix)

| Yêu cầu chức năng (FR) & Phi chức năng | User Story (US) | Tác nhân | Use Case (UC) | Mức ưu tiên |
| :--- | :--- | :--- | :--- | :--- |
| FR01: Báo cáo tổng doanh thu & lọc | US1 | Giám đốc | **UC01:** Xem báo cáo doanh thu | MUST |
| FR02: Cảnh báo giảm doanh thu 3 tháng | US2 | Giám đốc | **UC02:** Xem cảnh báo doanh thu | MUST |
| NFR03: Che giấu số điện thoại khách hàng | US3 | Admin | **UC04:** Thực thi luồng ETL | MUST |
| FR03: Phân tích tỉ lệ khách quay lại | US4 | Marketing | **UC05:** Phân tích tỷ lệ giữ chân | SHOULD |
| FR04: Ghi nhận dữ liệu lỗi định dạng | US5 | Admin | **UC04:** Thực thi luồng ETL | SHOULD |
| FR05: Xem và lọc chi tiết Reject Log | US6 | Admin | **UC03:** Xem nhật ký lỗi (Reject Log) | COULD |
| N
