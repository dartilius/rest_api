"""Bound WebSocket frames before buffering; preserve Gunicorn supervision."""

from uvicorn_worker import UvicornWorker


class RuntimeWorker(UvicornWorker):
    CONFIG_KWARGS = {
        "loop": "asyncio", "http": "h11", "ws": "websockets-sansio",
        "ws_max_size": 32768, "ws_ping_interval": 20, "ws_ping_timeout": 20,
        "ws_per_message_deflate": False,
    }
