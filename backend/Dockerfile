FROM python:3.10.11

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

RUN -p 9000:9000 \
   -p 9001:9001 \
   --name minio1 \
   --security-opt "credentialspec=file://path/to/file.json"
   -e "MINIO_ROOT_USER=ROOTUSER" \
   -e "MINIO_ROOT_PASSWORD=CHANGEME123" \
   -v D:\data:/data \
   quay.io/minio/minio server /data --console-address ":9001"

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "rmc_rest_api.wsgi"]