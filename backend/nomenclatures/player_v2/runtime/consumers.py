"""Authenticated Player publishing and session-protected admin subscriptions."""

import json
from importlib import import_module
from types import SimpleNamespace
from urllib.parse import urlsplit

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user
from django.http.request import validate_host

from nomenclatures.models import Nomenclature
from nomenclatures.player_v2.auth import lookup_station_token
from nomenclatures.player_v2.runtime.serializers import RuntimeSnapshotSerializer
from nomenclatures.player_v2.runtime.service import (
    CACHE_ERRORS,
    accept_runtime,
    display_snapshot,
    runtime_group,
)


def _origin_allowed(scope, *, native=False):
    headers = dict(scope.get("headers", []))
    origin = headers.get(b"origin")
    if origin is None:
        return native
    try:
        parsed = urlsplit(origin.decode())
        host = urlsplit("//" + headers.get(b"host", b"").decode())
        default_port = 443 if parsed.scheme == "https" else 80
        return (
            parsed.scheme in ("http", "https") and parsed.hostname is not None
            and parsed.hostname == host.hostname
            and (parsed.port or default_port) == (host.port or default_port)
            and validate_host(host.hostname, settings.ALLOWED_HOSTS)
        )
    except (UnicodeDecodeError, ValueError):
        return False


@database_sync_to_async
def _viewer(station_id, session_key):
    store = import_module(settings.SESSION_ENGINE).SessionStore(session_key=session_key)
    request = SimpleNamespace(session=store)
    request.user = get_user(request)
    if not request.user.is_active or not request.user.is_staff:
        return None
    obj = Nomenclature.objects.select_related("availability").filter(pk=station_id).first()
    if obj is None or not admin.site._registry[Nomenclature].has_view_permission(request, obj):
        return None
    try:
        last_answer = obj.availability.last_answer_date
    except AttributeError:
        last_answer = None
    return display_snapshot(station_id, legacy_state=obj.runtime_state, legacy_received=last_answer)


class RuntimeConsumer(AsyncJsonWebsocketConsumer):
    @classmethod
    async def encode_json(cls, content):
        return json.dumps(content, ensure_ascii=False, separators=(",", ":"), allow_nan=False)

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        if text_data is None or len(text_data.encode("utf-8")) > 32768:
            await self.close(code=1009)
            return
        try:
            await super().receive(text_data=text_data, **kwargs)
        except (ValueError, TypeError):
            await self.close(code=1008)


class PlayerRuntimeConsumer(RuntimeConsumer):
    # Publishing needs no receive subscription. Redis loss should not kill
    # this socket before the PostgreSQL reserve can accept a frame.
    channel_layer_alias = "runtime_publisher"

    async def connect(self):
        if not _origin_allowed(self.scope, native=True):
            await self.close(code=4403)
            return
        header = dict(self.scope.get("headers", [])).get(b"authorization", b"").decode(errors="replace")
        scheme, _, self.token = header.partition(" ")
        if scheme != "Station" or not self.token or " " in self.token:
            await self.close(code=4401)
            return
        credential = await database_sync_to_async(lookup_station_token)(self.token)
        if credential is None:
            await self.close(code=4401)
            return
        self.station_id = credential.nomenclature_id
        await self.accept()

    async def receive_json(self, content, **kwargs):
        # Re-check token rotation and rebinding, not only the handshake.
        credential = await database_sync_to_async(lookup_station_token)(self.token)
        if credential is None or credential.nomenclature_id != self.station_id:
            await self.close(code=4401)
            return
        serializer = RuntimeSnapshotSerializer(data=content)
        if not serializer.is_valid():
            await self.close(code=1008)
            return
        result = await database_sync_to_async(accept_runtime)(
            credential, serializer.validated_data, transport="websocket",
        )
        await self.send_json({"type": "runtime_ack",
                              "stream_id": str(serializer.validated_data["stream_id"]),
                              "sequence": serializer.validated_data["sequence"], **result})


class AdminRuntimeConsumer(RuntimeConsumer):
    async def connect(self):
        self.group = None
        if not _origin_allowed(self.scope):
            await self.close(code=4403)
            return
        session = self.scope.get("session")
        self.session_key = getattr(session, "session_key", None)
        self.station_id = self.scope["url_route"]["kwargs"]["station_id"]
        snapshot = await _viewer(self.station_id, self.session_key)
        if snapshot is None:
            await self.close(code=4403)
            return
        try:
            self.group = runtime_group(self.station_id)
            await self.channel_layer.group_add(self.group, self.channel_name)
        except CACHE_ERRORS:
            self.group = None
            await self.close(code=4503)
            return
        await self.accept()
        await self.send_json(snapshot)

    async def disconnect(self, close_code):
        if self.group:
            try:
                await self.channel_layer.group_discard(self.group, self.channel_name)
            except CACHE_ERRORS:
                pass

    async def receive_json(self, content, **kwargs):
        if not isinstance(content, dict) or content.get("type") != "ping":
            await self.close(code=1008)
            return
        snapshot = await _viewer(self.station_id, self.session_key)
        if snapshot is None:
            await self.close(code=4403)
            return
        await self.send_json({"type": "pong"})
        # A quiet/legacy station still needs a fresh/stale indication.
        await self.send_json(snapshot)

    async def runtime_changed(self, event):
        snapshot = await _viewer(self.station_id, self.session_key)
        if snapshot is None:
            await self.close(code=4403)
            return
        await self.send_json(snapshot)
