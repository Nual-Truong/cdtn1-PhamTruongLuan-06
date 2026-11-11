import pandas as pd
from src.transform.rules import chuan_hoa_dien_thoai, chuan_hoa_ten
from src.transform.gia_danh import tao_khoa_khach_hang


def che_so_dien_thoai(sdt):
    """Data Masking (NFR03): Che 4 số cuối của SĐT chuẩn 10 số."""
    if not sdt or len(str(sdt)) != 10:
        return None
    return str(sdt)[:6] + '****'


def lam_sach_khach_hang(df_tho):
    """
    HỢP ĐỒNG DỮ LIỆU:
    - Đầu vào: DataFrame khách hàng thô.
    - Đầu ra: (df_sach, df_reject).
    - Khóa khách hàng sử dụng HMAC-SHA256.
    - Reject chỉ lưu metadata, không lưu PII.
    """
    cot_reject = [
        'nguon', 'ma_ban_ghi', 'ma_quy_tac', 'ly_do', 'du_lieu_goc'
    ]

    if df_tho.empty:
        return pd.DataFrame(), pd.DataFrame(columns=cot_reject)

    df = df_tho.copy()
    df['sdt_chuan'] = df['so_dien_thoai'].apply(chuan_hoa_dien_thoai)
    df['ten_chuan'] = df['ho_ten'].apply(chuan_hoa_ten)

    mask_loi = df['sdt_chuan'].isna()
    df_sach = df[~mask_loi].copy()

    df_sach['khoa_khach_hang'] = df_sach.apply(
        lambda r: tao_khoa_khach_hang(r['ho_ten'], r['so_dien_thoai']),
        axis=1
    )
    df_sach['sdt_che'] = df_sach['sdt_chuan'].apply(che_so_dien_thoai)
    df_sach['ma_khach_gia_danh'] = df_sach['khoa_khach_hang']

    if mask_loi.sum() > 0:
        df_rej = df.loc[mask_loi].copy()

        df_rej['nguon'] = 'customers'

        if 'record_id' in df_rej.columns:
            df_rej['ma_ban_ghi'] = df_rej['record_id'].astype(str)
        else:
            df_rej['ma_ban_ghi'] = df_rej.index.astype(str)

        df_rej['ma_quy_tac'] = 'CL1'
        df_rej['ly_do'] = 'Số điện thoại không hợp lệ hoặc để trống'

        # Chỉ lưu metadata, tuyệt đối không serialize dòng dữ liệu gốc.
        df_rej['du_lieu_goc'] = df_rej.apply(
            lambda r: pd.Series({
                'nguon': 'customers',
                'ma_ban_ghi': r['ma_ban_ghi']
            }).to_json(force_ascii=False),
            axis=1
        )

        df_reject = df_rej[cot_reject].copy()
    else:
        df_reject = pd.DataFrame(columns=cot_reject)

    return df_sach, df_reject
