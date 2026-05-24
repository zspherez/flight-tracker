FROM python:3.12-slim

WORKDIR /app

# Install fli from local submodule (editable)
COPY fli /opt/fli
RUN pip install --no-cache-dir -e /opt/fli

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "127.0.0.1"]
