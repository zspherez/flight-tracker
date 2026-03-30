FROM python:3.12-slim

WORKDIR /app

# Install fli from local copy, patching line 191 to use 1 instead of 0
COPY fli /opt/fli
RUN sed -i '191s/0,  # constant/1,  # constant/' /opt/fli/fli/models/google_flights/flights.py \
    && pip install --no-cache-dir /opt/fli

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
