FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/
COPY dashboard/ ./dashboard/
COPY tests/ ./tests/
COPY sql/ ./sql/
COPY dataset/ ./dataset/
COPY .streamlit/ ./.streamlit/

# Prepare writable directories and non-root user
RUN mkdir -p /app/data /app/reports /app/docs/screenshots && \
    useradd -m appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8501

# Run ETL first, then start Streamlit only if ETL succeeds
CMD ["sh", "-c", "python -m src.pipeline && streamlit run dashboard/app.py --server.address=0.0.0.0 --server.port=8501"]