FROM python:3.13.6-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Устанавливаем инструменты для сборки
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip

COPY updated_req.txt .

RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r updated_req.txt

# --------------------------------------------------------------------- #

FROM python:3.13.6-slim

WORKDIR /app

RUN mkdir -p /app/network_logs

RUN apt-get update && apt-get install -y \
    curl \
    mediainfo \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/wheels /wheels

RUN pip install --no-cache /wheels/*
RUN rm -rf /root/.cache/pip


COPY . .

CMD ["bash", "/app/start.sh"]
