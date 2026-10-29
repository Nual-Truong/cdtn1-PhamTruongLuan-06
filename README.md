# Mekong Mobile - ETL Pipeline và Business Dashboard

Project mô phỏng quy trình xử lý dữ liệu bán hàng cho Mekong Mobile trong khuôn khổ
Chuyên đề tốt nghiệp 1. Hệ thống đọc dữ liệu CSV, làm sạch và kiểm tra chất lượng
dữ liệu, nạp vào kho dữ liệu SQLite theo star schema, sau đó hiển thị báo cáo trên
dashboard Streamlit.

Mekong Mobile và toàn bộ dữ liệu trong project là dữ liệu mô phỏng, chỉ phục vụ
mục đích học tập.

## Tính năng chính

- Đọc dữ liệu khách hàng, đơn hàng, chi tiết đơn hàng, sản phẩm và cửa hàng.

- Chuẩn hóa số điện thoại, ngày, tiền và các khóa nghiệp vụ.

- Tách các dòng không hợp lệ vào bảng `reject_rows` và ghi nhận kết quả kiểm tra chất lượng.

- Nạp dữ liệu vào SQLite star schema, gồm staging, dimension và fact tables.

- Cung cấp dashboard doanh thu theo khoảng ngày và tỉnh/thành phố.

- Hỗ trợ chạy pipeline theo khoảng ngày để xử lý backfill.

## Yêu cầu môi trường

- Python 3.10 trở lên.

- `pip`.

- SQLite, được tích hợp sẵn trong Python.

## Cài đặt

Mở terminal tại thư mục gốc của project:

```bash
python -m venv venv
```

Kích hoạt môi trường ảo:

```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

```bash
# Linux/macOS
source venv/bin/activate
```

Sau đó cài đặt các thư viện:

```bash
python -m pip install -r requirements.txt
```

## Chạy một lần toàn bộ project

Tại thư mục gốc, dùng lệnh tương ứng với terminal đang sử dụng.

> Nếu dòng lệnh bắt đầu bằng `PS E:\...>`, bạn đang dùng Windows PowerShell.
> Hãy chạy khối **Windows - PowerShell** bên dưới. Không dán lệnh Linux/macOS
> vào PowerShell và không dán dòng mở/đóng code block vào terminal.

### Windows - Command Prompt (CMD)

```cmd
python -m venv venv && .\venv\Scripts\activate && python -m pip install -r requirements.txt && pytest -q && python -m src.pipeline && streamlit run dashboard/app.py
```

### Windows - PowerShell

PowerShell 5.1 không hỗ trợ toán tử &&. Dùng lệnh sau:

```powershell
python -m venv venv; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; .\venv\Scripts\Activate.ps1; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; python -m pip install -r requirements.txt; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; pytest -q; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; python -m src.pipeline; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; streamlit run dashboard/app.py
```

Nếu PowerShell chặn kích hoạt môi trường ảo, chạy trước:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

### Linux/macOS - Terminal

> Chỉ chạy lệnh này trong Terminal dùng `bash` hoặc `zsh` trên Linux/macOS.
> Không chạy trong Windows PowerShell. PowerShell 5.1 không hỗ trợ `&&`,
> `source` hoặc lệnh kích hoạt môi trường `venv/bin/activate`.
>
> Trên Windows, dùng lệnh này trong **Git Bash** hoặc **WSL/Ubuntu** đã cài
> riêng. Gõ `bash` trong PowerShell không đảm bảo đã chuyển sang Git Bash/WSL;
> hãy mở ứng dụng Git Bash hoặc Ubuntu và kiểm tra prompt không còn bắt đầu bằng `PS`.

Dùng chuỗi lệnh sau để chạy liên tục các bước:

```bash
python3 -m venv venv && source venv/bin/activate && python3 -m pip install -r requirements.txt && pytest -q && python3 -m src.pipeline && streamlit run dashboard/app.py
```

Các chuỗi lệnh sẽ thực thi lần lượt. Sau khi Streamlit khởi động,
mở địa chỉ hiển thị trong terminal, thông thường là `http://localhost:8501`.
Nhấn `Ctrl+C` để dừng dashboard.

### Chạy nhanh sau khi đã cài đặt

Nếu đã tạo môi trường ảo và cài dependencies, có thể chạy kiểm thử, pipeline và
dashboard bằng một lệnh trong PowerShell:

```powershell
pytest -q; python -m src.pipeline; streamlit run dashboard/app.py
```

Trong PowerShell, dấu `;` cho phép chạy các lệnh liên tiếp. Streamlit sẽ giữ
terminal mở để phục vụ dashboard.

## Chạy pipeline

Pipeline mặc định đọc dữ liệu từ `dataset/`, tạo database tại `data/mekong_dw.db`
và ghi báo cáo/log vào `reports/`:

```bash
python -m src.pipeline
```

Chạy cho một khoảng ngày cụ thể:

```bash
python -m src.pipeline --tu-ngay 2026-06-01 --den-ngay 2026-06-30
```

Hai biến môi trường tùy chọn:

Windows PowerShell:

```powershell
$env:DATA_DIR = "dataset"
$env:DWH_URL = "sqlite:///data/mekong_dw.db"
python -m src.pipeline
```

- `DATA_DIR`: thư mục chứa các file CSV đầu vào, mặc định là `dataset`.
- `DWH_URL`: SQLAlchemy connection string, mặc định là `sqlite:///data/mekong_dw.db`.

## Chạy dashboard

Cần chạy pipeline trước để tạo database và các bảng dữ liệu:

```bash
streamlit run dashboard/app.py
```

Dashboard hiển thị tổng doanh thu, đơn hàng, khách hàng, doanh thu theo cửa hàng,
nhóm sản phẩm và tỷ lệ khách quay lại.

## Chạy kiểm thử

```bash
pytest -q
```

Bộ test tập trung vào chuẩn hóa số điện thoại, đọc ngày, làm sạch khách hàng/đơn
hàng và phát hiện sai lệch thành tiền.

## Cấu trúc thư mục

```text
dataset/       Dữ liệu CSV đầu vào
sql/           Script tạo bảng staging, reject và star schema
src/extract/   Đọc dữ liệu nguồn
src/transform/ Làm sạch và chuẩn hóa dữ liệu
src/quality/   Các kiểm tra chất lượng dữ liệu
src/load/      Nạp staging, reject và data warehouse
dashboard/     Ứng dụng báo cáo Streamlit
tests/         Kiểm thử tự động
reports/       Báo cáo chất lượng và log sau mỗi lần chạy
data/          SQLite database được tạo khi chạy pipeline
docs/          Tài liệu yêu cầu, kiến trúc, mô hình dữ liệu và triển khai
```

## Đầu ra sau khi chạy

- `data/mekong_dw.db`: kho dữ liệu SQLite.

- `reports/chat-luong-*.json`: kết quả kiểm tra chất lượng theo lô.

- `reports/run_*.log`: log của pipeline.

- Các bảng staging, reject, dimension và fact được tạo theo các script trong `sql/`.

## Dữ liệu và tài liệu tham khảo

- Mô tả đầy đủ các file CSV: [dataset/README.md](dataset/README.md).

- Yêu cầu hệ thống: [docs/srs.md](docs/srs.md).

- Từ điển dữ liệu: [docs/data-dictionary.md](docs/data-dictionary.md).

- Hướng dẫn chạy theo khoảng ngày: [docs/deployment-guide.md](docs/deployment-guide.md).

## Lưu ý

- Phải chạy lệnh từ thư mục gốc của project để các đường dẫn tương đối hoạt động đúng.

- Dashboard sẽ không hiển thị nếu `data/mekong_dw.db` chưa được tạo hoặc chưa có dữ liệu.

- Các lỗi dữ liệu trong bộ CSV là lỗi mô phỏng có chủ ý; chúng được dùng để đo lường
  và kiểm tra luồng làm sạch, không nên xóa trực tiếp khỏi dữ liệu nguồn.
