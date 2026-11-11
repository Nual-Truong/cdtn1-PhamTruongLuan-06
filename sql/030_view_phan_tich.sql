-- VIEW 1: View phân tích khách hàng đã ẩn toàn bộ cột PII gốc (ho_ten, so_dien_thoai, dia_chi)
DROP VIEW IF EXISTS v_khach_hang_phan_tich;
CREATE VIEW v_khach_hang_phan_tich AS
SELECT
    dc.customer_key AS customer_sk,
    dc.customer_id AS ma_khach_gia_danh,
    dc.city AS tinh_thanh,
    SUBSTR(CAST(dc.created_date AS TEXT), 1, 7) AS thang_tao
FROM dim_customer dc;

-- VIEW 2: View tổng hợp theo tỉnh/thành phố có ngưỡng nhóm tối thiểu >= 20 khách hàng
DROP VIEW IF EXISTS v_bao_cao_tinh;
CREATE VIEW v_bao_cao_tinh AS
SELECT
    ds.thanh_pho AS tinh_thanh,
    COUNT(DISTINCT fs.customer_key) AS so_khach,
    COUNT(fs.sales_key) AS tong_so_dong_ban,
    SUM(fs.thanh_tien) AS tong_doanh_thu,
    ROUND(CAST(SUM(fs.thanh_tien) AS REAL) / COUNT(DISTINCT fs.customer_key), 2) AS doanh_thu_tb_khach
FROM fact_sales fs
JOIN dim_store ds ON fs.store_key = ds.store_key
GROUP BY ds.thanh_pho
HAVING COUNT(DISTINCT fs.customer_key) >= 20;
