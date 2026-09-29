FROM python:3.11-slim

WORKDIR /app

COPY exporter.py .

RUN pip install --no-cache-dir prometheus-client

EXPOSE 8000

CMD ["python", "exporter.py", "--db", "/data/control.db", "--port", "8000"]
