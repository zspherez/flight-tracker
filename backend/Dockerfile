FROM python:3.12-slim

WORKDIR /app

# Install fli from local copy
COPY fli /opt/fli
RUN pip install --no-cache-dir /opt/fli

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
