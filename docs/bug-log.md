# NHẬT KÝ LỖI VÀ XỬ LÝ (BUG LOG) – SMART CRM MEKONG MOBILE
**Luồng nghiệp vụ:** Luồng L6 – Xây dựng Kho dữ liệu và Báo cáo BI phân tích bán hàng (Track DA)  
**Tổng số bug đã phát hiện và sửa:** 03 bug (01 Critical, 02 Major) – Tất cả đều có commit riêng và đã chạy lại test đạt 100% PASS.

---

## BUG-01 – Hàm chuẩn hóa tên không xử lý ký tự 'Đ/đ' tiếng Việt làm sai lệch khóa hợp nhất khách hàng
1. **Mã và mức độ:** BUG-01 · **MAJOR** – Làm sai lệch khóa định danh tổng hợp (khoa_khach_hang), khiến cùng một khách hàng có tên chứa chữ Đ/đ (khi nhập có dấu và không dấu) bị tách thành 2 khách hàng khác nhau trong dim_customer.
2. **Phát hiện bởi:** TC-07 ( test_TC07_chat_luong_chuan_hoa_ten_chu_d_va_khoa_hop_nhat trong tests/test_rules.py).
3. **Triệu chứng:** Khi gọi chuan_hoa_ten('Đặng Văn Đồng'), hệ thống trả về chuỗi 'đangvandong' (vẫn còn chữ 'đ'), không khớp với chuan_hoa_ten('Dang Van Dong') là 'dangvandong'.
4. **Cách tái lập:** Chạy lệnh pytest tests/test_rules.py -v -k "TC07" với dữ liệu thử ho_ten = 'Đặng Văn Đồng' và đối chiếu với 'Dang Van Dong'. Lỗi xuất hiện 100% ở mọi lần chạy.
5. **Nguyên nhân:** Trong bảng mã Unicode, ký tự 'đ' (U+0111) và 'Đ' (U+0110) là ký tự Latin có gạch ngang độc lập, không phải ký tự ghép dấu (Mn). Do đó unicodedata.normalize('NFD', str(raw)) trong src/transform/rules.py không tách được thành chữ 'd'.
6. **Cách sửa:** Cập nhật hàm chuan_hoa_ten(raw) trong tệp src/transform/rules.py: bổ sung bước .replace('đ', 'd').replace('Đ', 'd') trước khi gọi unicodedata.normalize('NFD', s), đồng thời kiểm tra an toàn chuỗi rỗng ở hàm doc_ngay.
7. **Link commit và xác nhận:** https://github.com/Nual-Truong/cdtn1-PhamTruongLuan-06/commit/49274f6b68b2e3da18b2344ddb37a7b1d8893530 — Đã chạy lại TC-07 -> **PASS** (chuan_hoa_ten('Đặng Văn Đồng') == 'dangvandong'); toàn bộ tests/test_rules.py đạt 7/7 PASS.

---

## BUG-02 – Tầng Transform bỏ sót các dòng chi tiết đơn hàng mồ côi (CL5), không đẩy vào bảng 
reject_rows
1. **Mã và mức độ:** BUG-02 · **CRITICAL** – Vi phạm tính toàn vẹn dữ liệu và hợp đồng bảng 
reject_rows: 153 dòng chi tiết đơn hàng mồ côi (order_id không tồn tại trong bảng orders hợp lệ) không được ghi nhận vào bảng 
reject_rows dù báo cáo chất lượng báo CL5 KHÔNG ĐẠT.
2. **Phát hiện bởi:** TC-10 ( test_TC10_du_lieu_sai_chi_tiet_don_hang_mo_coi_CL5 trong tests/test_checks.py) và đối chiếu báo cáo chất lượng lô dữ liệu thực tế.
3. **Triệu chứng:** Báo cáo chất lượng phát hiện 153 dòng vi phạm CL5, nhưng bảng 
reject_rows chỉ lưu 634 dòng lỗi (114 dòng CL2 + 520 dòng CL3), hoàn toàn không có bản ghi nào mang ma_quy_tac = 'CL5', còn df_itm_sach vẫn giữ nguyên các dòng mồ côi.
4. **Cách tái lập:** Gọi lam_sach_don_hang(df_ord, df_itm) với df_ord chỉ có order_id='100' và df_itm có dòng order_id='999', sau đó kiểm tra 'CL5' in set(df_reject['ma_quy_tac']) bằng lệnh pytest tests/test_checks.py -v -k "TC10".
5. **Nguyên nhân:** Hàm lam_sach_don_hang trong src/transform/clean_orders.py mới chỉ lập bộ lọc cho CL2 (sai ngày), CL4 (trùng khóa đơn) và CL3 (lệch thành tiền), nhưng thiếu hoàn toàn bước kiểm tra toàn vẹn tham chiếu itm_df['order_id'].isin(df_ord_sach['order_id']) (CL5).
6. **Cách sửa:** Trong src/transform/clean_orders.py, sau khi lọc CL3, bổ sung bước kiểm tra loi_mo_coi = ~itm_hop_le_tien['order_id'].astype(str).isin(set(df_ord_sach['order_id'].astype(str))), tách toàn bộ dòng vi phạm vào 
eject_list với ma_quy_tac = 'CL5' kèm lý do tiếng Việt và loại khỏi df_itm_sach.
7. **Link commit và xác nhận:** https://github.com/Nual-Truong/cdtn1-PhamTruongLuan-06/commit/7b84a4585878bb13789f0dbbe788c9202f4bec1b — Đã chạy lại TC-10 -> **PASS** (len(df_itm_sach) == 1 và df_reject có mã CL5); khi chạy lại pipeline thực tế, tổng số dòng trong 
reject_rows tăng từ 634 lên 787 dòng (634 + 153), khớp 100% với báo cáo chất lượng.

---

## BUG-03 – Pipeline truyền nhầm DataFrame đã lọc sạch vào hàm kiểm định CL1 và CL4 làm báo cáo chất lượng luôn báo 0 lỗi
1. **Mã và mức độ:** BUG-03 · **MAJOR** – Chức năng đo lường và giám sát chất lượng dữ liệu nguồn cho quy tắc CL1 (SĐT hợp lệ) và CL4 (Khóa đơn hàng duy nhất) trả về kết quả sai (luôn báo so_dong_loi = 0), làm mất khả năng cảnh báo chất lượng dữ liệu đầu vào.
2. **Phát hiện bởi:** TC-11 ( test_TC11_chat_luong_do_ba_chieu_va_kiem_dinh_du_lieu_goc trong tests/test_checks.py).
3. **Triệu chứng:** Khi đưa tập dữ liệu thô có chứa số điện thoại sai định dạng (CL1) và đơn hàng trùng mã (CL4) vào pipeline, tệp báo cáo 
eports/chat-luong-lo-toan-bo.json vẫn luôn ghi nhận CL1: so_dong_loi = 0 và CL4: so_dong_loi = 0.
4. **Cách tái lập:** Chạy pytest tests/test_checks.py -v -k "TC11" với tập dữ liệu thô có 1 dòng sai SĐT và 2 dòng trùng (ma_cua_hang, ma_don) rồi kiểm tra kết quả kiểm định của pipeline.
5. **Nguyên nhân:** Tại pha # 3. QUALITY trong src/pipeline.py, lập trình viên truyền nhầm biến df_cus_sach vào checks.cl1_dien_thoai_hop_le(df_cus_sach) và df_ord_sach vào checks.cl4_khoa_khong_trung(df_ord_sach) (là các DataFrame đã bị lọc bỏ dòng lỗi ở pha Transform trước đó) thay vì truyền dữ liệu thô trước khi lọc.
6. **Cách sửa:** Tách hàm kiem_dinh_chat_luong_lo(df_cus_tho, df_ord_tho, df_itm_tho) trong src/pipeline.py để đo CL1–CL5 trực tiếp trên bản sao dữ liệu thô đầu vào (df_cus_kiem, df_ord_kiem, df_itm_kiem), đồng thời tích hợp module src/quality/three_dimensions.py để tự động xuất bảng báo cáo 3 chiều 
eports/chat-luong.md (7 cột).
7. **Link commit và xác nhận:** https://github.com/Nual-Truong/cdtn1-PhamTruongLuan-06/commit/57c5bca0f7182697a307cfdd519e620941496650 — Đã chạy lại TC-11 -> **PASS** (CL1.so_dong_loi == 1, CL4.so_dong_loi == 2); chạy lệnh pytest -v toàn bộ 12/12 test cases đạt **100% PASS**.
