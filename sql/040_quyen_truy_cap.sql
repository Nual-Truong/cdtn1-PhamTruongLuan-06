-- Phân quyền truy cập theo vai trò (Role-Based Access Control - RBAC) cho Kho dữ liệu
-- Vai trò 1: Nhà phân tích (chỉ đọc VIEW đã giả danh hóa, KHÔNG có quyền SELECT trên dim_customer gốc)
CREATE ROLE nha_phan_tich;
GRANT USAGE ON SCHEMA public TO nha_phan_tich;
GRANT SELECT ON v_khach_hang_phan_tich, v_bao_cao_tinh, fact_sales, dim_store, dim_product, dim_date TO nha_phan_tich;

-- Vai trò 2: Nhân viên nghiệp vụ cửa hàng (chỉ xem dữ liệu thuộc cửa hàng của mình qua RLS)
CREATE ROLE nhan_vien_nghiep_vu;
GRANT USAGE ON SCHEMA public TO nhan_vien_nghiep_vu;
GRANT SELECT ON dim_customer, fact_sales TO nhan_vien_nghiep_vu;

ALTER TABLE fact_sales ENABLE ROW LEVEL SECURITY;

CREATE POLICY chi_cua_hang_cua_minh ON fact_sales FOR SELECT
    TO nhan_vien_nghiep_vu
    USING (store_key = current_setting('app.store_key')::INT);

CREATE POLICY phan_tich_doc_tat_ca ON fact_sales FOR SELECT
    TO nha_phan_tich
    USING (true);

-- Vai trò 3: Tài khoản Pipeline ETL (quyền tối thiểu SELECT, INSERT, UPDATE để nạp kho, không có DROP)
CREATE ROLE pipeline_writer;
GRANT USAGE ON SCHEMA public TO pipeline_writer;
GRANT SELECT, INSERT, UPDATE ON staging_customers, staging_orders, reject_rows, dim_store, dim_product, dim_date, dim_customer, fact_sales TO pipeline_writer;
CREATE POLICY pipeline_ghi ON fact_sales FOR ALL TO pipeline_writer USING (true) WITH CHECK (true);
