FROM python:3.11-slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN python -m pip install --upgrade pip
RUN apt update && apt install -y ffmpeg

COPY req.txt .

RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r req.txt

# --------------------------------------------------------------------- #

FROM python:3.11-slim

WORKDIR /app

RUN python -m pip install --upgrade pip

COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/req.txt .

RUN pip install --no-cache /wheels/*
RUN rm -rf /root/.cache/pip

COPY . .

RUN useradd uid0001
USER uid0001

ENTRYPOINT [ "./entrypoint.sh" ]
