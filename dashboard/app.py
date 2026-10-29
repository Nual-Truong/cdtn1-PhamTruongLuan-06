from typing import Optional

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text

# =========================================================
# 1. CẤU HÌNH VÀ GIAO DIỆN CHUNG
# =========================================================
st.set_page_config(
    page_title="Mekong Mobile | Business Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
    div[data-testid="stMetric"] {
        background: #f7f9fc;
        border: 1px solid #e7ebf2;
        padding: 14px 16px;
        border-radius: 12px;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #e4e8ef;
        border-radius: 10px;
        margin-bottom: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 MEKONG MOBILE")
st.caption("DASHBOARD PHÂN TÍCH KINH DOANH & GIÁM SÁT CHẤT LƯỢNG DỮ LIỆU")
st.divider()


# =========================================================
# 2. KẾT NỐI VÀ ĐỌC DỮ LIỆU
# =========================================================
@st.cache_resource
def lay_engine():
    return create_engine("sqlite:///data/mekong_dw.db", pool_pre_ping=True)


@st.cache_data(ttl=300)
def doc_du_lieu(sql: str, tham: Optional[dict] = None):
    with lay_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=tham or {})


def dinh_dang_tien(value):
    return f"{value:,.0f} ₫" if pd.notna(value) else "—"


def tao_loc_tinh(cot_thanh_pho: str, danh_sach_tinh: list):
    """Tạo điều kiện lọc có bind parameter, tránh ghép trực tiếp dữ liệu người dùng vào SQL."""
    if not danh_sach_tinh:
        return "", {}
    placeholders = []
    params = {}
    for i, tinh in enumerate(danh_sach_tinh):
        key = f"tinh_{i}"
        placeholders.append(f":{key}")
        params[key] = tinh
    return f" AND {cot_thanh_pho} IN ({', '.join(placeholders)})", params


def hien_loi_ket_noi(thong_bao: str, khoa_thu_lai: str):
    st.error(thong_bao)
    if st.button("🔄 Thử lại", key=khoa_thu_lai):
        doc_du_lieu.clear()
        lay_engine.clear()
        st.rerun()


# =========================================================
# 3. BỘ LỌC DÙNG CHUNG
# =========================================================
st.sidebar.header("🎛️ Bộ lọc báo cáo")
st.sidebar.caption("Các bộ lọc áp dụng cho những biểu đồ kinh doanh.")

try:
    danh_sach_tinh = doc_du_lieu(
        """
        SELECT DISTINCT thanh_pho
        FROM dim_store
        WHERE thanh_pho IS NOT NULL
          AND thanh_pho != 'Không xác định'
        ORDER BY thanh_pho
        """
    )["thanh_pho"].dropna().tolist()
except Exception:
    hien_loi_ket_noi(
        "Chưa thể kết nối tới kho dữ liệu để tải danh sách tỉnh/thành phố. "
        "Vui lòng thử lại.",
        "thu_lai_danh_sach_tinh",
    )
    st.stop()

tu_ngay = st.sidebar.date_input("Từ ngày", value=pd.Timestamp("2024-01-01").date())
den_ngay = st.sidebar.date_input("Đến ngày", value=pd.Timestamp("2026-12-31").date())
tinh_chon = st.sidebar.multiselect(
    "Tỉnh/Thành phố",
    options=danh_sach_tinh,
    placeholder="Tất cả tỉnh/thành phố",
)

if tu_ngay > den_ngay:
    st.sidebar.error("Ngày bắt đầu không được lớn hơn ngày kết thúc.")
    st.stop()

tu_sql = pd.to_datetime(tu_ngay).strftime("%Y-%m-%d")
den_sql = pd.to_datetime(den_ngay).strftime("%Y-%m-%d")
tu_hien_thi = pd.to_datetime(tu_ngay).strftime("%d/%m/%Y")
den_hien_thi = pd.to_datetime(den_ngay).strftime("%d/%m/%Y")

dk_tinh, tham_tinh = tao_loc_tinh("ds.thanh_pho", tinh_chon)
tham_ngay = {"tu": tu_sql, "den": den_sql, **tham_tinh}

st.caption(
    f"📅 Kỳ báo cáo: **{tu_hien_thi} – {den_hien_thi}**"
    + (f" · 📍 {', '.join(tinh_chon)}" if tinh_chon else " · 📍 Toàn bộ cửa hàng")
)


# =========================================================
# 4. TRUY VẤN DỮ LIỆU KINH DOANH
# =========================================================
with st.spinner("Đang tổng hợp dữ liệu kinh doanh..."):
    try:
        sql_doanh_thu = f"""
            SELECT ds.ten_cua_hang, SUM(f.thanh_tien) AS tong_doanh_thu
            FROM fact_sales f
            JOIN dim_store ds ON f.store_key = ds.store_key
            JOIN dim_date dn ON f.date_key = dn.date_key
            WHERE dn.full_date BETWEEN :tu AND :den
            {dk_tinh}
            GROUP BY ds.ten_cua_hang
            ORDER BY tong_doanh_thu DESC
        """
        df_doanh_thu = doc_du_lieu(sql_doanh_thu, tham_ngay)

        sql_san_pham = f"""
            SELECT dp.nhom_san_pham, SUM(f.thanh_tien) AS tong_doanh_thu
            FROM fact_sales f
            JOIN dim_product dp ON f.product_key = dp.product_key
            JOIN dim_store ds ON f.store_key = ds.store_key
            JOIN dim_date dn ON f.date_key = dn.date_key
            WHERE dn.full_date BETWEEN :tu AND :den
            {dk_tinh}
            GROUP BY dp.nhom_san_pham
            ORDER BY tong_doanh_thu DESC
        """
        df_san_pham = doc_du_lieu(sql_san_pham, tham_ngay)

        sql_kpi = f"""
            SELECT
                SUM(f.thanh_tien) AS tong_doanh_thu,
                COUNT(DISTINCT f.order_key) AS tong_don_hang,
                COUNT(DISTINCT CASE WHEN f.customer_key != -1 THEN f.customer_key END)
                    AS so_khach_hang
            FROM fact_sales f
            JOIN dim_store ds ON f.store_key = ds.store_key
            JOIN dim_date dn ON f.date_key = dn.date_key
            WHERE dn.full_date BETWEEN :tu AND :den
            {dk_tinh}
        """
        df_kpi = doc_du_lieu(sql_kpi, tham_ngay)

        sql_retention = f"""
            SELECT
                CASE WHEN so_don >= 2 THEN 'Khách quay lại (từ 2 đơn)'
                     ELSE 'Khách mua 1 lần' END AS nhom_khach,
                COUNT(*) AS so_luong
            FROM (
                SELECT f.customer_key, COUNT(DISTINCT f.order_key) AS so_don
                FROM fact_sales f
                JOIN dim_date dn ON f.date_key = dn.date_key
                JOIN dim_store ds ON f.store_key = ds.store_key
                WHERE f.customer_key != -1
                  AND dn.full_date BETWEEN :tu AND :den
                  {dk_tinh}
                GROUP BY f.customer_key
            ) t
            GROUP BY nhom_khach
        """
        df_retention = doc_du_lieu(sql_retention, tham_ngay)

    except Exception:
        hien_loi_ket_noi(
            "Chưa thể tải báo cáo kinh doanh do kết nối kho dữ liệu gặp sự cố. "
            "Vui lòng thử lại.",
            "thu_lai_bao_cao_kinh_doanh",
        )
        st.stop()


# =========================================================
# 5. TỔNG QUAN DÀNH CHO TỔNG GIÁM ĐỐC
# =========================================================
st.subheader("Tổng quan kinh doanh")

if df_doanh_thu.empty:
    st.info(
        "Không tìm thấy giao dịch trong kỳ báo cáo này. "
        "Hãy mở rộng khoảng ngày hoặc thay đổi bộ lọc khu vực."
    )
    st.stop()

kpi = df_kpi.iloc[0]
tong_doanh_thu = float(kpi["tong_doanh_thu"] or 0)
tong_don_hang = int(kpi["tong_don_hang"] or 0)
so_khach_hang = int(kpi["so_khach_hang"] or 0)
so_cua_hang = int(df_doanh_thu["ten_cua_hang"].nunique())
doanh_thu_tb = tong_doanh_thu / so_cua_hang if so_cua_hang else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Tổng doanh thu", dinh_dang_tien(tong_doanh_thu))
m2.metric("Tổng đơn hàng", f"{tong_don_hang:,}")
m3.metric("Khách hàng", f"{so_khach_hang:,}")
m4.metric("Cửa hàng có phát sinh", f"{so_cua_hang:,}")

st.divider()


# =========================================================
# 6. PHÂN TÍCH DOANH THU
# =========================================================
st.subheader("Phân tích doanh thu")
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("**1. Doanh thu theo cửa hàng**")
    fig1 = px.bar(
        df_doanh_thu.sort_values("tong_doanh_thu", ascending=True),
        x="tong_doanh_thu",
        y="ten_cua_hang",
        orientation="h",
        text="tong_doanh_thu",
        labels={"tong_doanh_thu": "Doanh thu (VNĐ)", "ten_cua_hang": "Cửa hàng"},
    )
    fig1.update_traces(
        texttemplate="%{x:,.0f}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{y}<br>Doanh thu: %{x:,.0f} VNĐ<extra></extra>",
    )
    fig1.update_layout(
        height=max(380, 42 * len(df_doanh_thu)),
        margin=dict(l=10, r=45, t=20, b=20),
        xaxis=dict(tickformat=",.0f", title="Doanh thu (VNĐ)"),
        yaxis_title="",
    )
    st.plotly_chart(fig1, use_container_width=True)
    st.caption(
        f"Trung bình: **{dinh_dang_tien(doanh_thu_tb)} / cửa hàng** · "
        f"{len(df_doanh_thu)} cửa hàng"
    )

with col2:
    st.markdown("**2. Doanh thu theo nhóm sản phẩm**")
    if not df_san_pham.empty:
        fig2 = px.bar(
            df_san_pham.sort_values("tong_doanh_thu", ascending=True),
            x="tong_doanh_thu",
            y="nhom_san_pham",
            orientation="h",
            text="tong_doanh_thu",
            color="tong_doanh_thu",
            color_continuous_scale="Blues",
            labels={"tong_doanh_thu": "Doanh thu (VNĐ)", "nhom_san_pham": "Nhóm sản phẩm"},
        )
        fig2.update_traces(
            texttemplate="%{x:,.0f}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}<br>Doanh thu: %{x:,.0f} VNĐ<extra></extra>",
        )
        fig2.update_layout(
            height=max(380, 42 * len(df_san_pham)),
            margin=dict(l=10, r=45, t=20, b=20),
            xaxis=dict(tickformat=",.0f", title="Doanh thu (VNĐ)"),
            yaxis_title="",
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Không có dữ liệu doanh thu theo nhóm sản phẩm trong kỳ này.")

st.divider()
st.subheader("Khách hàng quay lại mua hàng")
if not df_retention.empty:
    fig3 = px.pie(
        df_retention,
        names="nhom_khach",
        values="so_luong",
        hole=0.55,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig3.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label}<br>Số khách: %{value:,}<br>Tỷ lệ: %{percent}<extra></extra>",
    )
    fig3.update_layout(height=380, margin=dict(l=10, r=10, t=20, b=20))
    st.plotly_chart(fig3, use_container_width=True)
    st.caption("Phân loại theo số đơn hàng của từng khách trong kỳ báo cáo đã chọn.")
else:
    st.info("Chưa có dữ liệu khách hàng hợp lệ để tính tỷ lệ quay lại.")


# =========================================================
# 7. KHUNG 4 – CẢNH BÁO DOANH THU GIẢM LIÊN TIẾP
# =========================================================
st.divider()
st.subheader("⚠️ Cảnh báo cửa hàng có doanh thu giảm 3 tháng liên tiếp")
st.caption(
    "Điều kiện cảnh báo: doanh thu tháng N < tháng N-1 < tháng N-2. "
    "Bảng kiểm tra lịch sử theo tháng trong toàn bộ kho dữ liệu."
)

sql_canh_bao = f"""
    WITH DoanhThuThang AS (
        SELECT
            ds.ten_cua_hang,
            dn.year,
            dn.month,
            SUM(f.thanh_tien) AS doanh_thu
        FROM fact_sales f
        JOIN dim_store ds ON f.store_key = ds.store_key
        JOIN dim_date dn ON f.date_key = dn.date_key
        WHERE 1=1
        {dk_tinh}
        GROUP BY ds.ten_cua_hang, dn.year, dn.month
    ),
    XuHuong AS (
        SELECT
            ten_cua_hang,
            year,
            month,
            doanh_thu,
            LAG(doanh_thu, 1) OVER (
                PARTITION BY ten_cua_hang ORDER BY year, month
            ) AS thang_truoc_1,
            LAG(doanh_thu, 2) OVER (
                PARTITION BY ten_cua_hang ORDER BY year, month
            ) AS thang_truoc_2
        FROM DoanhThuThang
    )
    SELECT
        ten_cua_hang AS "Tên cửa hàng",
        printf('%02d/%d', month, year) AS "Tháng cảnh báo",
        thang_truoc_2 AS "Doanh thu (N-2)",
        thang_truoc_1 AS "Doanh thu (N-1)",
        doanh_thu AS "Doanh thu (N)"
    FROM XuHuong
    WHERE doanh_thu < thang_truoc_1
      AND thang_truoc_1 < thang_truoc_2
      AND doanh_thu > 0
      AND date(printf('%04d-%02d-01', year, month)) <= date(:den)
      AND date(printf('%04d-%02d-01', year, month), '+1 month', '-1 day') >= date(:tu)
    ORDER BY year DESC, month DESC, ten_cua_hang
"""

try:
    df_canh_bao = doc_du_lieu(sql_canh_bao, tham_ngay)
    if not df_canh_bao.empty:
        st.warning(f"Phát hiện **{len(df_canh_bao)}** trường hợp cần kiểm tra.")
        st.dataframe(
            df_canh_bao.style.format({
                "Doanh thu (N-2)": "{:,.0f} ₫",
                "Doanh thu (N-1)": "{:,.0f} ₫",
                "Doanh thu (N)": "{:,.0f} ₫",
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("Không phát hiện cửa hàng giảm doanh thu 3 tháng liên tiếp.")
except Exception:
    hien_loi_ket_noi(
        "Chưa thể tải cảnh báo doanh thu do kết nối kho dữ liệu gặp sự cố. "
        "Vui lòng thử lại.",
        "thu_lai_canh_bao_doanh_thu",
    )


# =========================================================
# 8. KHUNG 5 – GIÁM SÁT CHẤT LƯỢNG DỮ LIỆU (REJECT LOG)
# =========================================================
st.divider()
st.subheader("🛠️ Giám sát chất lượng dữ liệu")
st.caption(
    "Dành cho nhân viên vận hành dữ liệu: tra cứu các dòng bị loại khi nạp dữ liệu "
    "và xác định nguyên nhân cần xử lý."
)

# Khai báo tập trung: muốn thêm loại lỗi mới, chỉ cần thêm một phần tử vào danh sách này.
DANH_MUC_LOI = [
    {
        "ma": "CL1",
        "ten": "Lỗi số điện thoại",
        "mo_ta": "Số điện thoại bị thiếu, chứa ký tự không phải số hoặc không đúng định dạng 10 chữ số.",
        "kiem_tra": "Kiểm tra trường số điện thoại trong dữ liệu nguồn; chuẩn hóa đầu số và loại bỏ ký tự thừa.",
        "xu_ly": "Đối chiếu với thông tin khách hàng gốc. Không tự tạo số điện thoại nếu không có căn cứ.",
    },
    {
        "ma": "CL2",
        "ten": "Lỗi ngày tháng",
        "mo_ta": "Ngày giao dịch bị bỏ trống, không hợp lệ hoặc không đúng định dạng mà hệ thống yêu cầu.",
        "kiem_tra": "Kiểm tra ngày giao dịch, định dạng ngày và tính hợp lệ của giá trị ngày.",
        "xu_ly": "Đối chiếu hóa đơn/chứng từ để xác nhận ngày đúng, sau đó chuẩn hóa định dạng trước khi nạp lại.",
    },
    {
        "ma": "CL3",
        "ten": "Lỗi lệch thành tiền",
        "mo_ta": "Thành tiền không khớp với phép tính số lượng × đơn giá theo quy tắc dữ liệu hiện tại.",
        "kiem_tra": "So sánh số lượng, đơn giá, thành tiền và kiểm tra quy tắc chiết khấu/thuế nếu có.",
        "xu_ly": "Đối soát với hóa đơn hoặc hệ thống bán hàng trước khi điều chỉnh giá trị.",
    },
    {
        "ma": "CL4",
        "ten": "Lỗi trùng lặp",
        "mo_ta": "Một bản ghi hoặc đơn hàng có dấu hiệu được ghi nhận nhiều lần trong dữ liệu nạp.",
        "kiem_tra": "Kiểm tra mã đơn hàng, mã sản phẩm, thời điểm giao dịch và khóa định danh của bản ghi.",
        "xu_ly": "Xác minh bản ghi trùng thực sự trước khi loại bỏ; tránh xóa các dòng hợp lệ của cùng đơn hàng.",
    },
    {
        "ma": "CL5",
        "ten": "Lỗi mồ côi",
        "mo_ta": "Dòng dữ liệu chi tiết tham chiếu đến đơn hàng hoặc khóa liên kết không tồn tại/không xác định.",
        "kiem_tra": "Kiểm tra khóa ngoại và đối chiếu dữ liệu chi tiết với bảng đơn hàng/danh mục liên quan.",
        "xu_ly": "Khôi phục khóa tham chiếu từ nguồn đáng tin cậy hoặc chuyển bản ghi sang quy trình xử lý ngoại lệ.",
    },
]

# Các hộp có mũi tên đóng/mở. Có thể thêm CL6, CL7... trong DANH_MUC_LOI.
with st.expander("📚 Từ điển mã lỗi – nhấn để mở rộng/thu gọn", expanded=False):
    for loi in DANH_MUC_LOI:
        st.markdown(f"#### {loi['ma']}  |  {loi['ten']}")
        st.markdown(f"**Mô tả:** {loi['mo_ta']}")
        st.markdown(f"**Cần kiểm tra:** {loi['kiem_tra']}")
        st.markdown(f"**Hướng xử lý đề xuất:** {loi['xu_ly']}")

col_filter, col_data = st.columns([1, 2.6], gap="large")

with col_filter:
    st.markdown("**🔎 Lọc bản ghi lỗi**")
    lua_chon_loi = ["Tất cả các lỗi"] + [
        f"{loi['ma']} – {loi['ten']}" for loi in DANH_MUC_LOI
    ]
    ma_loi_chon = st.selectbox(
        "Chọn nhóm lỗi",
        options=lua_chon_loi,
        index=0,
    )
    so_dong_hien_thi = st.selectbox(
        "Số dòng hiển thị",
        options=[50, 100, 200, 500],
        index=1,
    )
    st.caption("Mặc định hiển thị các bản ghi mới nhất theo mã lô nạp.")

with col_data:
    try:
        tham_reject = {"gioi_han": int(so_dong_hien_thi)}
        dieu_kien_loc = ""
        if ma_loi_chon != "Tất cả các lỗi":
            ma_cl = ma_loi_chon.split(" – ")[0]
            dieu_kien_loc = "WHERE ma_quy_tac = :ma_loi"
            tham_reject["ma_loi"] = ma_cl

        sql_reject_detail = f"""
            SELECT
                batch_id AS "Mã lô nạp",
                ma_quy_tac AS "Mã lỗi",
                ly_do AS "Lý do bị loại",
                du_lieu_goc AS "Dữ liệu gốc (JSON)"
            FROM reject_rows
            {dieu_kien_loc}
            ORDER BY batch_id DESC
            LIMIT :gioi_han
        """
        df_reject_detail = doc_du_lieu(sql_reject_detail, tham_reject)

        if not df_reject_detail.empty:
            st.warning(
                f"Đang hiển thị **{len(df_reject_detail)}** bản ghi lỗi. "
                "Nhân viên nên kiểm tra lý do và dữ liệu gốc trước khi xử lý."
            )
            st.dataframe(
                df_reject_detail,
                use_container_width=True,
                hide_index=True,
                height=420,
            )
        else:
            st.success(
                f"Không tìm thấy bản ghi thuộc nhóm **{ma_loi_chon}** "
                "trong danh sách đang truy vấn."
            )
    except Exception:
        hien_loi_ket_noi(
            "Chưa thể tải nhật ký dữ liệu lỗi do kết nối kho dữ liệu gặp sự cố. "
            "Vui lòng thử lại.",
            "thu_lai_reject_log",
        )

st.caption(
    "Mekong Mobile · Dashboard nội bộ · Dữ liệu được làm mới theo bộ nhớ đệm 5 phút."
)
