# HƯỚNG DẪN TRIỂN KHAI VÀ HẸN LỊCH CHẠY PIPELINE (DEPLOYMENT GUIDE)

## 1. Chạy Pipeline theo tham số ngày và Chạy bù (Backfill)

Pipeline hỗ trợ tham số khoảng ngày và đảm bảo tính chất **chạy lại được (idempotent)**:

- Chạy toàn bộ dữ liệu: `python -m src.pipeline`
- Chạy theo khoảng ngày cụ thể: `python -m src.pipeline --tu-ngay 2026-06-01 --den-ngay 2026-06-30`
- Khi một lần chạy thất bại, thực hiện chạy bù bằng cách gọi lại đúng khoảng ngày đó mà không gây nhân đôi bản ghi.

## 2. Cấu hình hẹn lịch chạy tự động ban đêm (Batch Processing theo NFR02)

- **Trên Linux / macOS (Crontab):** Chạy lúc 02:00 sáng hàng ngày:
  ```cron
  0 2 * * * cd /duong-dan/Chuyen_de_1 && ./venv/bin/python -m src.pipeline >> reports/cron.log 2>&1
  ```
