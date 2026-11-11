import json
from datetime import datetime


# Allowlist: chỉ lưu các trường cần thiết cho Staging.
ALLOWLIST = {
    "staging_customers": [
        "record_id",
        "ngay_tao",
        "sdt_che",
        "khoa_khach_hang"
    ],
    "staging_orders": [
        "order_id",
        "ma_don",
        "ma_cua_hang",
        "ngay_chuan",
        "thanh_tien",
        "khoa_khach_hang"
    ]
}

COT_REJECT = [
    "nguon",
    "ma_ban_ghi",
    "ma_quy_tac",
    "ly_do",
    "du_lieu_goc"
]

KHOA_JSON_REJECT = {"nguon", "ma_ban_ghi"}


def ghi_lo(df_sach, batch_id, engine, table_name="staging_customers"):
    """Ghi dữ liệu sạch vào Staging theo danh sách cột an toàn."""

    if df_sach.empty:
        return

    if table_name not in ALLOWLIST:
        raise ValueError(f"Bang staging khong duoc phep: {table_name}")

    cot_duoc_phep = ALLOWLIST[table_name]

    cot_thieu = [
        cot for cot in cot_duoc_phep
        if cot not in df_sach.columns
    ]

    if cot_thieu:
        raise ValueError(
            f"Thieu cot bat buoc trong {table_name}: {cot_thieu}"
        )

    # Chỉ chọn các cột trong Allowlist.
    df_luu = df_sach[cot_duoc_phep].copy()
    df_luu["batch_id"] = batch_id

    # Giữ nguyên hành vi replace hiện tại.
    with engine.begin() as conn:
        df_luu.to_sql(
            table_name,
            conn,
            if_exists="replace",
            index=False
        )


def kiem_tra_json_reject(gia_tri):
    """Chỉ chấp nhận JSON chứa metadata, không chứa PII."""

    if gia_tri is None:
        raise ValueError("Reject JSON khong duoc de trong")

    try:
        du_lieu = json.loads(gia_tri)
    except (TypeError, json.JSONDecodeError):
        raise ValueError("Reject JSON khong hop le")

    if not isinstance(du_lieu, dict):
        raise ValueError("Reject JSON phai la object")

    if not set(du_lieu.keys()).issubset(KHOA_JSON_REJECT):
        raise ValueError("Reject JSON chua truong khong duoc phep")

    return json.dumps(du_lieu, ensure_ascii=False)


def ghi_reject(df_reject, batch_id, engine, table_name="reject_rows"):
    """Ghi Reject chỉ với metadata đã được kiểm tra."""

    if df_reject.empty:
        return

    cot_thieu = [
        cot for cot in COT_REJECT
        if cot not in df_reject.columns
    ]

    if cot_thieu:
        raise ValueError(f"Thieu cot Reject bat buoc: {cot_thieu}")

    df_luu = df_reject[COT_REJECT].copy()

    # Kiểm tra từng JSON để ngăn dữ liệu cá nhân lọt vào Reject.
    df_luu["du_lieu_goc"] = df_luu["du_lieu_goc"].apply(
        kiem_tra_json_reject
    )

    df_luu["batch_id"] = batch_id

    with engine.begin() as conn:
        df_luu.to_sql(
            table_name,
            conn,
            if_exists="replace",
            index=False
        )


def ghi_bao_cao(ket_qua_kiem, batch_id, so_dong_vao, so_reject):
    """Sinh báo cáo chất lượng dữ liệu dưới dạng JSON."""

    report = {
        "batch_id": batch_id,
        "thoi_gian": datetime.now().isoformat(),
        "tong_so_dong_vao": so_dong_vao,
        "so_dong_sach": so_dong_vao - so_reject,
        "so_dong_reject": so_reject,
        "chi_tiet_kiem_tra": [
            {
                "ma": kq.ma,
                "ten": kq.ten,
                "so_dong_kiem": kq.so_dong_kiem,
                "so_dong_loi": kq.so_dong_loi,
                "ti_le_loi": round(kq.ti_le_loi * 100, 2),
                "nguong_cho_phep": kq.nguong_cho_phep * 100,
                "ket_luan": "ĐẠT" if kq.dat else "KHÔNG ĐẠT"
            }
            for kq in ket_qua_kiem
        ]
    }

    file_name = f"reports/chat-luong-{batch_id}.json"

    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=4)

    return file_name