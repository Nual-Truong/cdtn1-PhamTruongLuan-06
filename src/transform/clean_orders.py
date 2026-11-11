import json
import pandas as pd

from src.transform.rules import doc_ngay, chuan_hoa_dien_thoai, chuan_hoa_ten
from src.transform.gia_danh import tao_khoa_khach_hang


COT_REJECT = [
    'nguon', 'ma_ban_ghi', 'ma_quy_tac', 'ly_do', 'du_lieu_goc'
]


def tao_reject(df, mask, nguon, cot_ma, ma_quy_tac, ly_do):
    """Tạo Reject chỉ chứa metadata, không lưu dữ liệu cá nhân."""
    if not mask.any():
        return pd.DataFrame(columns=COT_REJECT)

    rej = df.loc[mask].copy()

    if cot_ma in rej.columns:
        ma_ban_ghi = rej[cot_ma].astype(str)
    else:
        ma_ban_ghi = pd.Series(rej.index.astype(str), index=rej.index)

    result = pd.DataFrame(index=rej.index)
    result['nguon'] = nguon
    result['ma_ban_ghi'] = ma_ban_ghi
    result['ma_quy_tac'] = ma_quy_tac
    result['ly_do'] = ly_do

    result['du_lieu_goc'] = [
        json.dumps({
            'nguon': nguon,
            'ma_ban_ghi': str(ma)
        }, ensure_ascii=False)
        for ma in ma_ban_ghi
    ]

    return result[COT_REJECT].reset_index(drop=True)


def lam_sach_don_hang(df_orders_tho, df_items_tho):
    """
    HỢP ĐỒNG DỮ LIỆU:
    - Đầu vào: DataFrame orders và order_items thô.
    - Đầu ra: (df_ord_sach, df_itm_sach, df_reject_gop).
    - Khóa khách hàng sử dụng HMAC-SHA256.
    - Reject chỉ lưu metadata, không lưu PII.
    """
    if df_orders_tho.empty or df_items_tho.empty:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(columns=COT_REJECT)
        )

    # 1. Chuẩn hóa Orders
    ord_df = df_orders_tho.copy()
    ord_df['ngay_chuan'] = ord_df['ngay'].apply(doc_ngay)
    ord_df['sdt_chuan'] = ord_df['so_dien_thoai'].apply(
        chuan_hoa_dien_thoai
    )
    ord_df['ten_chuan'] = ord_df['ten_khach'].apply(chuan_hoa_ten)

    ord_df['khoa_khach_hang'] = ord_df.apply(
        lambda r: tao_khoa_khach_hang(
            r['ten_khach'],
            r['so_dien_thoai']
        ),
        axis=1
    )

    ord_df['thanh_tien'] = pd.to_numeric(
        ord_df['thanh_tien'], errors='coerce'
    ).fillna(0)

    loi_ngay = ord_df['ngay_chuan'].isna()
    loi_trung = ord_df.duplicated(
        subset=['ma_cua_hang', 'ma_don'],
        keep='first'
    )

    reject_ord_mask = loi_ngay | loi_trung
    df_ord_sach = ord_df[~reject_ord_mask].copy()

    reject_list = []

    if reject_ord_mask.any():
        # CL2 duoc uu tien neu mot dong dong thoi vi pham CL2 va CL4.
        cac_nhom_loi = [
            (
                'CL2',
                loi_ngay,
                'Ngày giao dịch sai định dạng hoặc để trống'
            ),
            (
                'CL4',
                loi_trung & ~loi_ngay,
                'Trùng khóa đơn hàng (ma_cua_hang, ma_don)'
            )
        ]

        for ma, mask, ly_do in cac_nhom_loi:
            if mask.any():
                reject_list.append(
                    tao_reject(
                        ord_df,
                        mask,
                        'orders',
                        'order_id',
                        ma,
                        ly_do
                    )
                )
    # 2. Chuẩn hóa Order Items
    itm_df = df_items_tho.copy()

    # Ma dinh danh duy nhat cho tung dong trong file order_items.
    # On dinh khi cung file va thu tu dong duoc giu nguyen.
    itm_df['_ma_ban_ghi'] = [
        f'ORDER_ITEM_ROW_{i + 1:06d}'
        for i in range(len(itm_df))
    ]

    for cot in ['so_luong', 'don_gia', 'thanh_tien']:
        itm_df[cot] = pd.to_numeric(
            itm_df[cot], errors='coerce'
        ).fillna(0).astype(int)

    loi_tien = (
        itm_df['thanh_tien']
        - itm_df['so_luong'] * itm_df['don_gia']
    ).abs() > 1

    if loi_tien.any():
        reject_list.append(
            tao_reject(
                itm_df,
                loi_tien,
                'order_items',
                '_ma_ban_ghi',
                'CL3',
                'Thành tiền không khớp số lượng nhân đơn giá'
            )
        )

    itm_hop_le_tien = itm_df[~loi_tien].copy()

    # 3. Kiểm tra khóa ngoại CL5
    tap_order_hop_le = set(
        df_ord_sach['order_id'].astype(str)
    )

    loi_mo_coi = ~itm_hop_le_tien['order_id'].astype(
        str
    ).isin(tap_order_hop_le)

    if loi_mo_coi.any():
        reject_list.append(
            tao_reject(
                itm_hop_le_tien,
                loi_mo_coi,
                'order_items',
                '_ma_ban_ghi',
                'CL5',
                'Chi tiết đơn hàng không tham chiếu đến đơn hàng hợp lệ'
            )
        )

    df_itm_sach = itm_hop_le_tien[~loi_mo_coi].copy()

    df_reject_gop = (
        pd.concat(reject_list, ignore_index=True)
        if reject_list
        else pd.DataFrame(columns=COT_REJECT)
    )

    return df_ord_sach, df_itm_sach, df_reject_gop
