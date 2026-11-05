import pandas as pd
from sqlalchemy import create_engine
from src.transform.clean_customers import lam_sach_khach_hang
from src.transform.clean_orders import lam_sach_don_hang
from src.load.load_warehouse import nap_kho_du_lieu
from src.pipeline import khoi_tao_database_tu_sql, kiem_dinh_chat_luong_lo

def test_TC08_luong_dung_hop_dong_lam_sach_khach_hang_CL1():
    """TC-08 (Luồng đúng - Integration): Hợp đồng làm sạch khách hàng giữ dòng đúng và đẩy dòng sai SĐT vào reject CL1."""
    df_mau = pd.DataFrame([
        {'record_id': '1', 'ho_ten': 'Nguyễn Văn A', 'so_dien_thoai': '0912345678', 'ngay_tao': '2025-01-01'},
        {'record_id': '2', 'ho_ten': 'Trần Thị B', 'so_dien_thoai': 'sdt_rac_123', 'ngay_tao': '2025-01-02'}
    ])
    df_sach, df_reject = lam_sach_khach_hang(df_mau)

    for cot_bat_buoc in ['sdt_chuan', 'ten_chuan', 'khoa_khach_hang']:
        assert cot_bat_buoc in df_sach.columns
    assert len(df_sach) == 1
    assert len(df_reject) == 1
    assert df_reject.iloc[0]['ma_quy_tac'] == 'CL1'

def test_TC09_du_lieu_sai_don_hang_sai_ngay_CL2_va_trung_ma_CL4():
    """TC-09 (Dữ liệu sai - Integration): Tách dòng đơn hàng sai ngày (CL2), trùng mã (CL4) và lệch tiền (CL3) vào reject."""
    df_ord = pd.DataFrame([
        {'order_id': '1', 'ma_don': 'HD01', 'ma_cua_hang': 'MM001', 'ngay': '17/08/2025', 'ten_khach': 'A', 'so_dien_thoai': '0912345678', 'thanh_tien': '2000'},
        {'order_id': '2', 'ma_don': 'HD01', 'ma_cua_hang': 'MM001', 'ngay': '17/08/2025', 'ten_khach': 'A', 'so_dien_thoai': '0912345678', 'thanh_tien': '2000'},
        {'order_id': '3', 'ma_don': 'HD02', 'ma_cua_hang': 'MM001', 'ngay': 'ngay-sai', 'ten_khach': 'B', 'so_dien_thoai': '0912345679', 'thanh_tien': '1000'},
    ])
    df_itm = pd.DataFrame([
        {'order_id': '1', 'product_id': '10', 'so_luong': '2', 'don_gia': '1000', 'thanh_tien': '2000'},
        {'order_id': '1', 'product_id': '11', 'so_luong': '2', 'don_gia': '1000', 'thanh_tien': '9999'},
    ])
    df_ord_sach, df_itm_sach, df_reject = lam_sach_don_hang(df_ord, df_itm)
    assert len(df_ord_sach) == 1
    assert len(df_itm_sach) == 1
    assert set(df_reject['ma_quy_tac']) == {'CL2', 'CL3', 'CL4'}

def test_TC10_du_lieu_sai_chi_tiet_don_hang_mo_coi_CL5():
    """TC-10 (Dữ liệu sai - Integration): Dòng order_items trỏ về order_id không tồn tại phải bị loại và ghi vào reject với mã CL5."""
    df_ord = pd.DataFrame([
        {'order_id': '100', 'ma_don': 'HD100', 'ma_cua_hang': 'MM001', 'ngay': '17/08/2025', 'ten_khach': 'A', 'so_dien_thoai': '0912345678', 'thanh_tien': '2000'}
    ])
    df_itm = pd.DataFrame([
        {'order_id': '100', 'product_id': '10', 'so_luong': '2', 'don_gia': '1000', 'thanh_tien': '2000'},
        {'order_id': '999', 'product_id': '11', 'so_luong': '1', 'don_gia': '1000', 'thanh_tien': '1000'},
    ])
    _, df_itm_sach, df_reject = lam_sach_don_hang(df_ord, df_itm)
    assert len(df_itm_sach) == 1
    assert 'CL5' in set(df_reject['ma_quy_tac'])

def test_TC11_chat_luong_do_ba_chieu_va_kiem_dinh_du_lieu_goc():
    """TC-11 (Chất lượng dữ liệu - System): Kiểm định CL1-CL5 và đo 3 chiều trên dữ liệu thô phải phát hiện đúng số lỗi gốc."""
    df_cus_tho = pd.DataFrame([
        {'record_id': '1', 'ho_ten': 'Nguyen A', 'so_dien_thoai': '0912345678', 'email': '', 'ngay_tao': '2025-01-01'},
        {'record_id': '2', 'ho_ten': 'Tran B', 'so_dien_thoai': 'sai_sdt', 'email': '', 'ngay_tao': '2025-01-02'},
    ])
    df_ord_tho = pd.DataFrame([
        {'order_id': '1', 'ma_don': 'HD01', 'ma_cua_hang': 'MM001', 'ngay': '17/08/2025', 'ten_khach': 'A', 'so_dien_thoai': '0912345678', 'thanh_tien': '1000'},
        {'order_id': '2', 'ma_don': 'HD01', 'ma_cua_hang': 'MM001', 'ngay': '17/08/2025', 'ten_khach': 'A', 'so_dien_thoai': '0912345678', 'thanh_tien': '1000'},
    ])
    df_itm_tho = pd.DataFrame([
        {'order_id': '1', 'product_id': '10', 'so_luong': '1', 'don_gia': '1000', 'thanh_tien': '1000'},
    ])
    ket_qua = kiem_dinh_chat_luong_lo(df_cus_tho, df_ord_tho, df_itm_tho)
    kq_map = {k.ma: k for k in ket_qua}
    assert kq_map['CL1'].so_dong_loi == 1
    assert kq_map['CL4'].so_dong_loi == 2

def test_TC12_tai_lap_chay_pipeline_hai_lan_khong_nhan_doi(tmp_path):
    """TC-12 (Tính tái lập - System): Chạy nạp kho dữ liệu Star Schema 2 lần liên tiếp không làm nhân đôi bản ghi."""
    db_file = tmp_path / "test_dw.db"
    engine = create_engine(f"sqlite:///{db_file}")
    khoi_tao_database_tu_sql(engine)

    df_cus_tho = pd.DataFrame([{
        'record_id': '1', 'customer_id': '1', 'ho_ten': 'Nguyễn Văn A', 'full_name': 'Nguyễn Văn A',
        'so_dien_thoai': '0912345678', 'phone': '0912345678', 'email': 'a@test.com',
        'dia_chi': 'HCM', 'address': 'HCM', 'tinh_thanh': 'TP.HCM', 'province': 'TP.HCM', 'thanh_pho': 'TP.HCM', 'ngay_tao': '2025-01-01'
    }])
    df_ord_tho = pd.DataFrame([{
        'order_id': '1', 'ma_don': 'HD01', 'order_code': 'HD01', 'ma_cua_hang': 'MM001', 'store_code': 'MM001',
        'ngay': '17/08/2025', 'ten_khach': 'Nguyễn Văn A', 'so_dien_thoai': '0912345678', 'thanh_tien': '2000'
    }])
    df_itm_tho = pd.DataFrame([{
        'item_id': '1', 'order_id': '1', 'product_id': 'P01', 'product_code': 'SP01', 'ma_san_pham': 'SP01',
        'ten_san_pham': 'Điện thoại X', 'nhom_san_pham': 'Điện thoại cao cấp',
        'so_luong': '2', 'don_gia': '1000', 'thanh_tien': '2000'
    }])
    df_str_tho = pd.DataFrame([{
        'store_id': '1', 'store_code': 'MM001', 'ma_cua_hang': 'MM001',
        'store_name': 'Mekong Q1', 'ten_cua_hang': 'Mekong Q1',
        'province': 'TP.HCM', 'city': 'TP.HCM', 'tinh_thanh': 'TP.HCM', 'thanh_pho': 'TP.HCM',
        'region': 'Đông Nam Bộ', 'khu_vuc': 'Đông Nam Bộ', 'address': 'Q1', 'dia_chi': 'Q1'
    }])
    df_prd_tho = pd.DataFrame([{
        'product_id': 'P01', 'product_code': 'SP01', 'sku': 'SP01', 'ma_san_pham': 'SP01',
        'product_name': 'Điện thoại X', 'ten_san_pham': 'Điện thoại X',
        'category': 'Điện thoại cao cấp', 'nhom_san_pham': 'Điện thoại cao cấp',
        'brand': 'BrandX', 'thuong_hieu': 'BrandX',
        'price': 1000, 'unit_price': 1000, 'list_price': 1000, 'don_gia': 1000, 'gia_niem_yet': 1000
    }])

    df_cus_sach, _ = lam_sach_khach_hang(df_cus_tho)
    df_ord_sach, df_itm_sach, _ = lam_sach_don_hang(df_ord_tho, df_itm_tho)

    lan_1 = nap_kho_du_lieu(df_cus_sach, df_ord_sach, df_itm_sach, df_str_tho, df_prd_tho, engine)
    lan_2 = nap_kho_du_lieu(df_cus_sach, df_ord_sach, df_itm_sach, df_str_tho, df_prd_tho, engine)

    assert lan_1 == lan_2
    assert lan_2['fact_sales'] == 1
