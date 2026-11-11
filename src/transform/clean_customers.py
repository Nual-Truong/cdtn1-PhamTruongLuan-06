import pandas as pd
from src.transform.rules import chuan_hoa_dien_thoai, chuan_hoa_ten
from src.transform.gia_danh import gia_danh

def che_so_dien_thoai(sdt):
    """Data Masking (NFR03): Che 4 số cuối của SĐT chuẩn 10 số."""
    if not sdt or len(str(sdt)) != 10:
        return None
    return str(sdt)[:6] + '****'

def lam_sach_khach_hang(df_tho):
    """
    HỢP ĐỒNG DỮ LIỆU (Data Contract):
    - Đầu vào: DataFrame khách hàng thô từ pha Extract.
    - Đầu ra: (df_sach, df_reject)
      df_sach gồm sdt_chuan, ten_chuan, khoa_khach_hang, sdt_che, ma_khach_gia_danh.
    """
    if df_tho.empty:
        return pd.DataFrame(), pd.DataFrame()

    df = df_tho.copy()
    df['sdt_chuan'] = df['so_dien_thoai'].apply(chuan_hoa_dien_thoai)
    df['ten_chuan'] = df['ho_ten'].apply(chuan_hoa_ten)

    mask_loi = df['sdt_chuan'].isna()
    df_sach = df[~mask_loi].copy()
    df_sach['khoa_khach_hang'] = df_sach['sdt_chuan'] + '_' + df_sach['ten_chuan']
    df_sach['sdt_che'] = df_sach['sdt_chuan'].apply(che_so_dien_thoai)
    df_sach['ma_khach_gia_danh'] = df_sach['sdt_chuan'].apply(gia_danh)

    if mask_loi.sum() > 0:
        df_rej = df[mask_loi].copy()
        df_rej['ma_quy_tac'] = 'CL1'
        df_rej['ly_do'] = 'Số điện thoại không hợp lệ hoặc để trống'
        df_rej['du_lieu_goc'] = df_rej.apply(lambda r: r.to_json(force_ascii=False), axis=1)
        df_reject = df_rej[['ma_quy_tac', 'ly_do', 'du_lieu_goc']]
    else:
        df_reject = pd.DataFrame(columns=['ma_quy_tac', 'ly_do', 'du_lieu_goc'])

    return df_sach, df_reject
