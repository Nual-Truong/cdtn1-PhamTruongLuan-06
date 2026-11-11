FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 1. Sao chép tệp khoá phiên bản trước để tận dụng Docker layer cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 2. Sao chép mã nguồn, bộ kiểm thử, kịch bản SQL, cấu hình và dữ liệu mẫu
COPY src/ ./src/
COPY tests/ ./tests/
COPY sql/ ./sql/
COPY dataset/ ./dataset/
COPY .streamlit/ ./.streamlit/

# 3. Tạo thư mục lưu CSDL kho dữ liệu, báo cáo và phân quyền cho non-root user
RUN mkdir -p /app/data /app/reports /app/docs/screenshots && \
    useradd -m appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8501

# Khi container khởi động: tự động chạy ETL Pipeline nạp dữ liệu mẫu vào kho,
# sau đó mở cổng HTTP health/report server tại 8501 để phục vụ kiểm tra trạng thái healthy
CMD ["sh", "-c", "python -m src.pipeline && python -m http.server 8501 --directory reports"]
