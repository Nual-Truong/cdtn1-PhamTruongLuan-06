import pandas as pd

def nap_kho_du_lieu(df_cus_sach, df_ord_sach, df_itm_sach, df_stores, df_products, engine):
    
    # ... (Giữ nguyên phần tạo dim_store và dim_product) ...
    dim_store = pd.DataFrame({
        'store_key': pd.to_numeric(df_stores['store_id'], errors='coerce').fillna(-1).astype(int),
        'ma_cua_hang': df_stores['store_code'].astype(str),
        'ten_cua_hang': df_stores['store_name'].astype(str),
        'thanh_pho': df_stores['thanh_pho'].astype(str),
        'quan_huyen': df_stores['quan_huyen'].astype(str),
        'ngay_khai_truong': df_stores['ngay_khai_truong'].astype(str)
    })
    unknown_store = pd.DataFrame([{'store_key': -1, 'ma_cua_hang': 'UNKNOWN', 'ten_cua_hang': 'Không xác định', 'thanh_pho': 'Không xác định', 'quan_huyen': 'Không xác định', 'ngay_khai_truong': '1970-01-01'}])
    dim_store = pd.concat([unknown_store, dim_store], ignore_index=True)

    dim_product = pd.DataFrame({
        'product_key': pd.to_numeric(df_products['product_id'], errors='coerce').fillna(-1).astype(int),
        'ma_san_pham': df_products['product_code'].astype(str),
        'ten_san_pham': df_products['product_name'].astype(str),
        'nhom_san_pham': df_products['nhom_san_pham'].astype(str),
        'thuong_hieu': df_products['thuong_hieu'].astype(str)
    })
    unknown_product = pd.DataFrame([{'product_key': -1, 'ma_san_pham': 'UNKNOWN', 'ten_san_pham': 'Không xác định', 'nhom_san_pham': 'Không xác định', 'thuong_hieu': 'Không xác định'}])
    dim_product = pd.concat([unknown_product, dim_product], ignore_index=True)

    # 3. Bảng dim_date (CHUẨN HÓA LẠI ĐỊNH DẠNG YYYY-MM-DD ĐỂ TRUY VẤN SQL CHUẨN XÁC)
    df_ord_sach['ngay_chuan'] = pd.to_datetime(df_ord_sach['ngay_chuan'], errors='coerce')
    dates = df_ord_sach['ngay_chuan'].dropna().unique()
    dates = pd.Series(dates).sort_values()
    
    dim_date = pd.DataFrame({
        'date_key': dates.dt.strftime('%Y%m%d').astype(int),
        'full_date': dates.dt.strftime('%Y-%m-%d'), # Định dạng này là bắt buộc để BETWEEN hoạt động
        'month': dates.dt.month,
        'quarter': dates.dt.quarter,
        'year': dates.dt.year
    })
    unknown_date = pd.DataFrame([{'date_key': -1, 'full_date': '1970-01-01', 'month': 1, 'quarter': 1, 'year': 1970}])
    dim_date = pd.concat([unknown_date, dim_date], ignore_index=True)

    # 4. Bảng dim_customer (Giữ nguyên)
    cus_dedup = df_cus_sach.drop_duplicates(subset=['khoa_khach_hang'], keep='last').reset_index(drop=True)
    cus_dedup['customer_key'] = cus_dedup.index + 1
    cus_dedup['sdt_masked'] = cus_dedup['sdt_chuan'].apply(
        lambda s: str(s)[:6] + '****' if pd.notna(s) and len(str(s)) == 10 else 'KHONG_SDT'
    )
    dim_customer = pd.DataFrame({
        'customer_key': cus_dedup['customer_key'],
        'khoa_khach_hang': cus_dedup['khoa_khach_hang'].astype(str),
        'sdt': cus_dedup['sdt_masked'],
        'phan_khuc': 'THUONG_XUYEN',
        'hieu_luc_tu': cus_dedup['ngay_tao'],
        'hieu_luc_den': '9999-12-31',
        'la_ban_ghi_hien_tai': 1
    })
    unknown_cus = pd.DataFrame([{'customer_key': -1, 'khoa_khach_hang': 'UNKNOWN', 'sdt': 'UNKNOWN', 'phan_khuc': 'UNKNOWN', 'hieu_luc_tu': '1970-01-01', 'hieu_luc_den': '9999-12-31', 'la_ban_ghi_hien_tai': 1}])
    dim_customer = pd.concat([unknown_cus, dim_customer], ignore_index=True)

    # 5. Bảng fact_sales (BẢO ĐẢM KHÓA NGÀY KHỚP 100% VỚI DIM_DATE)
    m_ord = df_ord_sach[['order_id', 'ma_cua_hang', 'ma_don', 'ngay_chuan', 'khoa_khach_hang']].copy()
    m_ord['order_key'] = m_ord['ma_cua_hang'].astype(str) + '_' + m_ord['ma_don'].astype(str)
    
    # Ép kiểu date_key giống hệt dim_date
    m_ord['date_key'] = pd.to_datetime(m_ord['ngay_chuan'], errors='coerce').dt.strftime('%Y%m%d').fillna(-1).astype(int)

    m_ord['order_id'] = m_ord['order_id'].astype(str)
    df_itm_sach['order_id'] = df_itm_sach['order_id'].astype(str)
    
    fact = df_itm_sach.merge(m_ord, on='order_id', how='inner')
    
    fact['ma_cua_hang'] = fact['ma_cua_hang'].astype(str)
    dim_store['ma_cua_hang'] = dim_store['ma_cua_hang'].astype(str)
    fact = fact.merge(dim_store[['store_key', 'ma_cua_hang']], on='ma_cua_hang', how='left')
    fact['store_key'] = fact['store_key'].fillna(-1).astype(int)

    fact['product_key'] = pd.to_numeric(fact['product_id'], errors='coerce').fillna(-1).astype(int)
    fact.loc[~fact['product_key'].isin(dim_product['product_key']), 'product_key'] = -1

    fact['khoa_khach_hang'] = fact['khoa_khach_hang'].astype(str)
    fact = fact.merge(dim_customer[['customer_key', 'khoa_khach_hang']], on='khoa_khach_hang', how='left')
    fact['customer_key'] = fact['customer_key'].fillna(-1).astype(int)

    fact_sales = fact.groupby(
        ['order_key', 'product_key', 'date_key', 'store_key', 'customer_key'], as_index=False
    ).agg({
        'so_luong': 'sum',
        'don_gia': 'first',
        'thanh_tien': 'sum'
    })

    with engine.begin() as conn:
        dim_store.to_sql('dim_store', conn, if_exists='replace', index=False)
        dim_product.to_sql('dim_product', conn, if_exists='replace', index=False)
        dim_date.to_sql('dim_date', conn, if_exists='replace', index=False)
        dim_customer.to_sql('dim_customer', conn, if_exists='replace', index=False)
        fact_sales.to_sql('fact_sales', conn, if_exists='replace', index=False)

    return {
        'dim_store': len(dim_store),
        'dim_product': len(dim_product),
        'dim_date': len(dim_date),
        'dim_customer': len(dim_customer),
        'fact_sales': len(fact_sales)
    }