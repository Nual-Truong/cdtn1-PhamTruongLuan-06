from datetime import date
import pandas as pd
from src.transform import rules
from src.quality import checks

def test_TC01_luong_dung_chuan_hoa_dien_thoai():
    """TC-01 (Luồng đúng - Unit): Chuẩn hóa 4 định dạng số điện thoại hợp lệ về 10 chữ số bắt đầu bằng 0."""
    du_lieu_thu = [
        ('0763247885', '0763247885'),
        ('0760.833.592', '0760833592'),
        ('076 083 3592', '0760833592'),
        ('+84760833592', '0760833592'),
    ]
    for tho, mong_doi in du_lieu_thu:
        assert rules.chuan_hoa_dien_thoai(tho) == mong_doi

def test_TC02_luong_dung_doc_ba_khuon_ngay():
    """TC-02 (Luồng đúng - Unit): Đọc chính xác 3 khuôn dạng ngày giao dịch (%d/%m/%Y, %d-%m-%y, %Y.%m.%d)."""
    assert rules.doc_ngay('17/08/2025') == date(2025, 8, 17)
    assert rules.doc_ngay('17-8-25') == date(2025, 8, 17)
    assert rules.doc_ngay('2025.08.17') == date(2025, 8, 17)

def test_TC03_gia_tri_bien_do_dai_sdt_9_10_11():
    """TC-03 (Giá trị biên - Unit): Kiểm tra ranh giới độ dài SĐT (9 số -> None, 10 số -> Hợp lệ, 11 số -> None)."""
    assert rules.chuan_hoa_dien_thoai('076083359') is None
    assert rules.chuan_hoa_dien_thoai('0760833592') == '0760833592'
    assert rules.chuan_hoa_dien_thoai('07608335921') is None

def test_TC04_gia_tri_bien_duoi_thanh_tien_lech_1_dong_CL3():
    """TC-04 (Giá trị biên trong ngưỡng - Unit): CL3 cho phép sai số làm tròn <= 1 đồng (lệch 0 và 1 đồng -> ĐẠT)."""
    df_bien_trong = pd.DataFrame([
        {'so_luong': 2, 'don_gia': 1000, 'thanh_tien': 2000}, # Lệch 0 đồng
        {'so_luong': 2, 'don_gia': 1000, 'thanh_tien': 2001}, # Biên trong: lệch đúng 1 đồng
    ])
    kq = checks.cl3_tien_khop(df_bien_trong, nguong=0.0)
    assert kq.so_dong_loi == 0
    assert kq.dat is True

def test_TC05_gia_tri_bien_tren_thanh_tien_lech_2_dong_CL3():
    """TC-05 (Giá trị biên ngoài ngưỡng - Unit): CL3 bắt lỗi ngay khi lệch 2 đồng (> 1 đồng -> Bị tính là dòng lỗi)."""
    df_bien_ngoai = pd.DataFrame([
        {'so_luong': 2, 'don_gia': 1000, 'thanh_tien': 2002}, # Biên ngoài: lệch 2 đồng
    ])
    kq = checks.cl3_tien_khop(df_bien_ngoai, nguong=0.0)
    assert kq.so_dong_loi == 1
    assert kq.dat is False

def test_TC06_du_lieu_sai_sdt_va_ngay_rong_rac():
    """TC-06 (Dữ liệu sai - Unit): Từ chối giá trị None, chuỗi rỗng, khoảng trắng và chuỗi rác không làm sập hàm."""
    for gia_tri_sai in [None, '', '   ', 'abc', '32/13/2025']:
        assert rules.chuan_hoa_dien_thoai(gia_tri_sai) is None
        assert rules.doc_ngay(gia_tri_sai) is None

def test_TC07_chat_luong_chuan_hoa_ten_chu_d_va_khoa_hop_nhat():
    """TC-07 (Chất lượng dữ liệu - Unit): Chuẩn hóa họ tên có chữ Đ/đ phải về d để gộp đúng khóa khách hàng."""
    assert rules.chuan_hoa_ten('Đặng Văn Đồng') == 'dangvandong'
    assert rules.khoa_hop_nhat('Đặng Văn Đồng', '0901.234.567') == rules.khoa_hop_nhat('Dang Van Dong', '0901234567')
