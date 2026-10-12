"""
ASGI config for rmc_rest_api project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rmc_rest_api.settings')

application = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from nomenclatures.player_v2.runtime.consumers import AdminRuntimeConsumer, PlayerRuntimeConsumer

application = ProtocolTypeRouter({
    "http": application,
    "websocket": URLRouter([
        path("ws/station/v2/runtime/", PlayerRuntimeConsumer.as_asgi()),
        path("ws/admin/nomenclatures/<uuid:station_id>/runtime/",
             AuthMiddlewareStack(AdminRuntimeConsumer.as_asgi())),
    ]),
})
