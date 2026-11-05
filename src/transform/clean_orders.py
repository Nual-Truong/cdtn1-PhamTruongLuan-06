import pandas as pd
from src.transform.rules import doc_ngay, chuan_hoa_dien_thoai, chuan_hoa_ten, khoa_hop_nhat

def lam_sach_don_hang(df_orders_tho, df_items_tho):
    """
    HỢP ĐỒNG DỮ LIỆU (Data Contract):
    - Đầu vào: 2 DataFrame thô (orders và order_items) từ pha Extract.
    - Đầu ra: (df_ord_sach, df_itm_sach, df_reject_gop)
    - Hành vi khi sai: Các dòng sai định dạng ngày (CL2), trùng khóa (CL4),
      lệch thành tiền (CL3) hoặc mồ côi khóa ngoại order_id (CL5) được tách riêng vào df_reject_gop kèm lý do.
    """
    if df_orders_tho.empty or df_items_tho.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # 1. Chuẩn hóa bảng Orders
    ord_df = df_orders_tho.copy()
    ord_df['ngay_chuan'] = ord_df['ngay'].apply(doc_ngay)
    ord_df['sdt_chuan'] = ord_df['so_dien_thoai'].apply(chuan_hoa_dien_thoai)
    ord_df['ten_chuan'] = ord_df['ten_khach'].apply(chuan_hoa_ten)
    ord_df['khoa_khach_hang'] = (
        ord_df['sdt_chuan'].fillna('KHONG_SDT') + '_' + ord_df['ten_chuan']
    )
    ord_df['thanh_tien'] = pd.to_numeric(ord_df['thanh_tien'], errors='coerce').fillna(0)

    # Lọc lỗi CL2 (Ngày không đọc được) & CL4 (Trùng cặp ma_cua_hang + ma_don)
    loi_ngay = ord_df['ngay_chuan'].isna()
    loi_trung = ord_df.duplicated(subset=['ma_cua_hang', 'ma_don'], keep='first')
    reject_ord_mask = loi_ngay | loi_trung

    df_ord_sach = ord_df[~reject_ord_mask].copy()

    reject_list = []
    if reject_ord_mask.sum() > 0:
        rej_o = ord_df[reject_ord_mask].copy()
        rej_o['ma_quy_tac'] = rej_o['ngay_chuan'].isna().map(lambda x: 'CL2' if x else 'CL4')
        rej_o['ly_do'] = rej_o['ma_quy_tac'].map(
            lambda m: 'Ngày giao dịch sai định dạng hoặc để trống' if m == 'CL2' else 'Trùng khóa đơn hàng (ma_cua_hang, ma_don)'
        )
        rej_o['du_lieu_goc'] = rej_o.apply(lambda r: r.to_json(force_ascii=False), axis=1)
        reject_list.append(rej_o[['ma_quy_tac', 'ly_do', 'du_lieu_goc']])

    # 2. Chuẩn hóa bảng Order Items
    itm_df = df_items_tho.copy()
    itm_df['so_luong'] = pd.to_numeric(itm_df['so_luong'], errors='coerce').fillna(0).astype(int)
    itm_df['don_gia'] = pd.to_numeric(itm_df['don_gia'], errors='coerce').fillna(0).astype(int)
    itm_df['thanh_tien'] = pd.to_numeric(itm_df['thanh_tien'], errors='coerce').fillna(0).astype(int)

    # Lọc lỗi CL3 (thanh_tien != so_luong * don_gia)
    loi_tien = (itm_df['thanh_tien'] - itm_df['so_luong'] * itm_df['don_gia']).abs() > 1
    if loi_tien.sum() > 0:
        rej_i_cl3 = itm_df[loi_tien].copy()
        rej_i_cl3['ma_quy_tac'] = 'CL3'
        rej_i_cl3['ly_do'] = rej_i_cl3.apply(
            lambda r: f"thanh_tien ({r['thanh_tien']}) khac so_luong ({r['so_luong']}) x don_gia ({r['don_gia']})",
            axis=1
        )
        rej_i_cl3['du_lieu_goc'] = rej_i_cl3.apply(lambda r: r.to_json(force_ascii=False), axis=1)
        reject_list.append(rej_i_cl3[['ma_quy_tac', 'ly_do', 'du_lieu_goc']])

    itm_hop_le_tien = itm_df[~loi_tien].copy()

    # Lọc lỗi CL5 (Mỗi dòng chi tiết hàng hóa phải trỏ về một đơn hàng hợp lệ có thật - Sửa BUG-02)
    tap_order_hop_le = set(df_ord_sach['order_id'].astype(str))
    loi_mo_coi = ~itm_hop_le_tien['order_id'].astype(str).isin(tap_order_hop_le)
    if loi_mo_coi.sum() > 0:
        rej_i_cl5 = itm_hop_le_tien[loi_mo_coi].copy()
        rej_i_cl5['ma_quy_tac'] = 'CL5'
        rej_i_cl5['ly_do'] = rej_i_cl5.apply(
            lambda r: f"Dong chi tiet don hang co order_id ({r['order_id']}) khong ton tai trong bang orders hop le",
            axis=1
        )
        rej_i_cl5['du_lieu_goc'] = rej_i_cl5.apply(lambda r: r.to_json(force_ascii=False), axis=1)
        reject_list.append(rej_i_cl5[['ma_quy_tac', 'ly_do', 'du_lieu_goc']])

    df_itm_sach = itm_hop_le_tien[~loi_mo_coi].copy()

    df_reject_gop = pd.concat(reject_list, ignore_index=True) if reject_list else pd.DataFrame(columns=['ma_quy_tac', 'ly_do', 'du_lieu_goc'])
    return df_ord_sach, df_itm_sach, df_reject_gop
