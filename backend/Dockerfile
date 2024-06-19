FROM python:3.11-slim

WORKDIR /app

COPY req.txt .

RUN pip install -r req.txt --no-cache-dir \
    apt-get update && apt-get install ffmpeg -y

COPY . .

CMD ["gunicorn", "--bind", "0:8000", "--workers", "8", "rmc_rest_api.wsgi"]