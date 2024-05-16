FROM python:3.10.11

WORKDIR /app

COPY req.txt .

RUN pip install -r req.txt --no-cache-dir

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "rmc_rest_api.wsgi"]