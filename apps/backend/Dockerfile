FROM python:3.12-slim

WORKDIR /app

# Install dependencies (cached layer — only rebuilds when requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Remove local dev .env so secrets come from Cloud Run environment variables only
RUN rm -f .env

EXPOSE 8000

# Cloud Run sends traffic to a single container; FastAPI is async so 1 worker
# handles concurrent requests efficiently. Cloud Run scales via instances.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--timeout-keep-alive", "75"]
