FROM python:3.12-slim

WORKDIR /app

# Install fli from local copy, patch line 191 (0 -> 1), editable install
COPY fli /opt/fli
RUN sed -i '191s/            0,  # constant/            1,  # constant/' /opt/fli/fli/models/google_flights/flights.py \
    && pip install --no-cache-dir -e /opt/fli

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
