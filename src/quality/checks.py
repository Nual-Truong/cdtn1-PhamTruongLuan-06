from dataclasses import dataclass
import pandas as pd

@dataclass
class KetQuaKiem:
    ma: str
    ten: str
    so_dong_kiem: int
    so_dong_loi: int
    nguong_cho_phep: float # Tỉ lệ lỗi tối đa cho phép

    @property
    def ti_le_loi(self):
        return self.so_dong_loi / self.so_dong_kiem if self.so_dong_kiem else 0.0

    @property
    def dat(self):
        return self.ti_le_loi <= self.nguong_cho_phep

def cl1_dien_thoai_hop_le(df, nguong=0.10):
    """Kiểm tra số lượng SĐT bị sai định dạng (không thể chuẩn hóa được)."""
    loi = df['sdt_chuan'].isna() & df['so_dien_thoai'].notna() & (df['so_dien_thoai'].astype(str).str.strip() != '')
    return KetQuaKiem('CL1', 'Số điện thoại chuẩn hoá được', len(df), int(loi.sum()), nguong)

def cl2_ngay_hop_le(df, nguong=0.01):
    """Kiểm tra số lượng ngày tháng không khớp với 3 khuôn dạng đã định nghĩa."""
    loi = df['ngay_chuan'].isna()
    return KetQuaKiem('CL2', 'Ngày đọc được theo một trong ba khuôn', len(df), int(loi.sum()), nguong)

def cl3_tien_khop(df, nguong=0.02):
    """Kiểm tra doanh thu: Thành tiền phải bằng Số lượng * Đơn giá."""
    loi = (df['thanh_tien'] - df['so_luong'] * df['don_gia']).abs() > 1
    return KetQuaKiem('CL3', 'thanh_tien = so_luong x don_gia', len(df), int(loi.sum()), nguong)

def cl4_khoa_khong_trung(df, nguong=0.0):
    """Kiểm tra mã đơn hàng bị trùng lặp giữa các cửa hàng."""
    loi = df.duplicated(subset=['ma_cua_hang', 'ma_don'], keep=False)
    return KetQuaKiem('CL4', 'Cặp (ma_cua_hang, ma_don) là duy nhất', len(df), int(loi.sum()), nguong)

def cl5_khoa_ngoai_ton_tai(df_items, df_orders, nguong=0.0):
    """Kiểm tra tính toàn vẹn: Dòng chi tiết đơn hàng phải trỏ về một đơn hàng có thật."""
    hop_le = df_items['order_id'].astype(str).isin(df_orders['order_id'].astype(str))
    return KetQuaKiem('CL5', 'Mỗi dòng hàng trỏ về một đơn hàng có thật', len(df_items), int((~hop_le).sum()), nguong)