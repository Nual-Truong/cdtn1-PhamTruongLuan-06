import pandas as pd
from dataclasses import dataclass

@dataclass
class Do:
    chieu: str       # DAY_DU | CHINH_XAC | NHAT_QUAN
    doi_tuong: str   # tên bảng.cột hoặc tên quy tắc
    so_kiem: int
    so_dat: int
    nguong: float

    @property
    def ti_le(self):
        return self.so_dat / self.so_kiem if self.so_kiem else 0.0

    @property
    def dat(self):
        return self.ti_le >= self.nguong

# CHIỀU 1: ĐẦY ĐỦ (COMPLETENESS) - Đo theo TỪNG CỘT với ngưỡng riêng
NGUONG_DAY_DU_CUSTOMERS = {
    'record_id': 1.0,
    'ho_ten': 0.999,
    'so_dien_thoai': 0.90,
    'email': 0.0,
    'ngay_tao': 0.999,
}

NGUONG_DAY_DU_ORDERS = {
    'order_id': 1.0,
    'ma_don': 0.999,
    'ma_cua_hang': 0.999,
    'ngay': 0.999,
}

def do_day_du(df, ten_bang, nguong_dict=None):
    if nguong_dict is None:
        nguong_dict = NGUONG_DAY_DU_CUSTOMERS if ten_bang == 'customers' else NGUONG_DAY_DU_ORDERS
    kq = []
    for cot, nguong in nguong_dict.items():
        if cot not in df.columns:
            continue
        co_gia_tri = df[cot].notna() & (df[cot].astype(str).str.strip() != '')
        kq.append(Do('DAY_DU', f'{ten_bang}.{cot}', len(df), int(co_gia_tri.sum()), nguong))
    return kq

# CHIỀU 2: CHÍNH XÁC (ACCURACY) - Đối chiếu quy tắc nghiệp vụ
def do_chinh_xac(df_items, df_orders, df_customers):
    kq = []
    # Quy tắc 1 (CL3): thanh_tien = so_luong x don_gia (sai số làm tròn <= 1 đồng)
    khop_tien = (df_items['thanh_tien'] - df_items['so_luong'] * df_items['don_gia']).abs() <= 1
    kq.append(Do('CHINH_XAC', 'order_items.thanh_tien = so_luong x don_gia', len(df_items), int(khop_tien.sum()), 0.98))

    # Quy tắc 2 (CL1): Số điện thoại khách hàng chuẩn hóa được thành 10 chữ số
    co_sdt = df_customers['so_dien_thoai'].notna() & (df_customers['so_dien_thoai'].astype(str).str.strip() != '')
    chuan_sdt = df_customers.loc[co_sdt, 'sdt_chuan'].notna()
    kq.append(Do('CHINH_XAC', 'customers.so_dien_thoai chuẩn hoá được', int(co_sdt.sum()), int(chuan_sdt.sum()), 0.90))

    # Quy tắc 3 (CL2): Ngày đơn hàng đọc được theo 1 trong 3 khuôn chuẩn
    hop_le_ngay = df_orders['ngay_chuan'].notna()
    kq.append(Do('CHINH_XAC', 'orders.ngay đọc được theo 3 khuôn', len(df_orders), int(hop_le_ngay.sum()), 0.99))
    return kq

# CHIỀU 3: NHẤT QUÁN (CONSISTENCY) - Giữa các bảng và khóa duy nhất
def do_nhat_quan(df_items, df_orders):
    kq = []
    # Phép kiểm 1 (CL5): Toàn vẹn tham chiếu order_items.order_id -> orders.order_id
    hop_le_fk = df_items['order_id'].astype(str).isin(set(df_orders['order_id'].astype(str)))
    kq.append(Do('NHAT_QUAN', 'order_items.order_id -> orders.order_id', len(df_items), int(hop_le_fk.sum()), 1.0))

    # Phép kiểm 2 (CL4): Khóa nghiệp vụ duy nhất (ma_cua_hang, ma_don)
    khong_trung = ~df_orders.duplicated(subset=['ma_cua_hang', 'ma_don'], keep=False)
    kq.append(Do('NHAT_QUAN', 'orders (ma_cua_hang, ma_don) duy nhất', len(df_orders), int(khong_trung.sum()), 1.0))

    # Phép kiểm 3: Số lượng bán trong chi tiết đơn hàng phải > 0
    so_luong_duong = df_items['so_luong'] > 0
    kq.append(Do('NHAT_QUAN', 'order_items.so_luong > 0', len(df_items), int(so_luong_duong.sum()), 1.0))
    return kq

def sinh_bao_cao(tat_ca_do, duong_dan='reports/chat-luong.md'):
    dong = [
        '| Chiều | Đối tượng | Số kiểm | Số đạt | Tỉ lệ | Ngưỡng | Kết luận |',
        '|---|---|---:|---:|---:|---:|---|'
    ]
    for d in tat_ca_do:
        ket_luan = 'ĐẠT' if d.dat else '**KHÔNG ĐẠT**'
        dong.append(
            f'| {d.chieu} | {d.doi_tuong} | {d.so_kiem} | {d.so_dat} | '
            f'{d.ti_le:.2%} | {d.nguong:.2%} | {ket_luan} |'
        )
    khong_dat = [d for d in tat_ca_do if not d.dat]
    dong.append('')
    dong.append(f'**Tổng: {len(tat_ca_do)} phép đo, {len(khong_dat)} không đạt.**')
    with open(duong_dan, 'w', encoding='utf-8') as f:
        f.write('\n'.join(dong))
    return khong_dat
