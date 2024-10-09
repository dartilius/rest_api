FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN python -m pip install --upgrade pip

COPY req.txt .

RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r req.txt

# --------------------------------------------------------------------- #

FROM python:3.11-slim

WORKDIR /app

RUN apt update && apt install -y curl mediainfo

COPY --from=builder /app/wheels /wheels

RUN pip install --no-cache /wheels/*
RUN rm -rf /root/.cache/pip

COPY . .

# RUN useradd uid0001
# USER uid0001

CMD ["bash", "/app/start.sh"]
