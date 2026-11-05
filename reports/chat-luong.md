| Chiều | Đối tượng | Số kiểm | Số đạt | Tỉ lệ | Ngưỡng | Kết luận |
|---|---|---:|---:|---:|---:|---|
| DAY_DU | customers.record_id | 67037 | 67037 | 100.00% | 100.00% | ĐẠT |
| DAY_DU | customers.ho_ten | 67037 | 67037 | 100.00% | 99.90% | ĐẠT |
| DAY_DU | customers.so_dien_thoai | 67037 | 62904 | 93.83% | 90.00% | ĐẠT |
| DAY_DU | customers.email | 67037 | 36880 | 55.01% | 0.00% | ĐẠT |
| DAY_DU | customers.ngay_tao | 67037 | 67037 | 100.00% | 99.90% | ĐẠT |
| DAY_DU | orders.order_id | 26000 | 26000 | 100.00% | 100.00% | ĐẠT |
| DAY_DU | orders.ma_don | 26000 | 26000 | 100.00% | 99.90% | ĐẠT |
| DAY_DU | orders.ma_cua_hang | 26000 | 26000 | 100.00% | 99.90% | ĐẠT |
| DAY_DU | orders.ngay | 26000 | 25886 | 99.56% | 99.90% | **KHÔNG ĐẠT** |
| CHINH_XAC | order_items.thanh_tien = so_luong x don_gia | 35697 | 35177 | 98.54% | 98.00% | ĐẠT |
| CHINH_XAC | customers.so_dien_thoai chuẩn hoá được | 62904 | 62904 | 100.00% | 90.00% | ĐẠT |
| CHINH_XAC | orders.ngay đọc được theo 3 khuôn | 26000 | 25886 | 99.56% | 99.00% | ĐẠT |
| NHAT_QUAN | order_items.order_id -> orders.order_id | 35024 | 35024 | 100.00% | 100.00% | ĐẠT |
| NHAT_QUAN | orders (ma_cua_hang, ma_don) duy nhất | 25886 | 25886 | 100.00% | 100.00% | ĐẠT |
| NHAT_QUAN | order_items.so_luong > 0 | 35024 | 35024 | 100.00% | 100.00% | ĐẠT |

**Tổng: 15 phép đo, 1 không đạt.**