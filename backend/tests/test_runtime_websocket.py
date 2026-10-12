"""Real ASGI routes: token publishing, admin sessions, origins and revocation."""

import asyncio
import json

import pytest
from asgiref.testing import ApplicationCommunicator
from channels.db import database_sync_to_async
from importlib import import_module
from django.conf import settings
from django.test import override_settings

from nomenclatures.models import StationCredential
from nomenclatures.player_v2.credentials import hash_station_token
from nomenclatures.player_v2.runtime import service as runtime_live
from rmc_rest_api.asgi import application
from tests.test_runtime_live import Cache, frame


def socket(path, headers=()):
    return ApplicationCommunicator(application, {
        "type": "websocket", "path": path, "raw_path": path.encode(), "root_path": "",
        "scheme": "ws", "headers": [(b"host", b"testserver"), *headers],
        "query_string": b"", "subprotocols": [], "server": ("testserver", 80), "client": ("127.0.0.1", 1234),
    })


async def disconnect(peer):
    await peer.send_input({"type": "websocket.disconnect", "code": 1000})
    await peer.wait(timeout=5)


@pytest.mark.django_db(transaction=True)
@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}, ALLOWED_HOSTS=["testserver"])
def test_token_publish_reaches_authorized_viewer_and_not_cross_origin(client, super_user, nomenclature, monkeypatch):
    token = "socket-contract-token"
    StationCredential.objects.create(nomenclature=nomenclature, token_hash=hash_station_token(token))
    fake = Cache()
    monkeypatch.setattr(runtime_live, "cache", fake)
    client.force_login(super_user)
    cookie = f"{settings.SESSION_COOKIE_NAME}={client.cookies[settings.SESSION_COOKIE_NAME].value}".encode()
    path = f"/ws/admin/nomenclatures/{nomenclature.pk}/runtime/"

    async def run():
        viewer = socket(path, [(b"cookie", cookie), (b"origin", b"http://testserver")])
        await viewer.send_input({"type": "websocket.connect"})
        assert (await viewer.receive_output(timeout=5))["type"] == "websocket.accept"
        await viewer.receive_output(timeout=5)  # bootstrap snapshot
        producer = socket("/ws/station/v2/runtime/", [(b"authorization", f"Station {token}".encode())])
        await producer.send_input({"type": "websocket.connect"})
        assert (await producer.receive_output(timeout=5))["type"] == "websocket.accept"
        await producer.send_input({"type": "websocket.receive", "text": json.dumps(frame(name="Прямой эфир"))})
        ack = json.loads((await producer.receive_output(timeout=5))["text"])
        assert ack["accepted"] is True
        update = json.loads((await viewer.receive_output(timeout=5))["text"])
        assert update["content"]["background"][0]["name"] == "Прямой эфир"
        # An open socket must not keep privileges after logout or rotation.
        session_key = client.cookies[settings.SESSION_COOKIE_NAME].value
        await database_sync_to_async(import_module(settings.SESSION_ENGINE).SessionStore(session_key=session_key).delete)()
        await viewer.send_input({"type": "websocket.receive", "text": '{"type":"ping"}'})
        assert (await viewer.receive_output(timeout=5))["code"] == 4403
        await database_sync_to_async(StationCredential.objects.filter(nomenclature=nomenclature).update)(is_active=False)
        await producer.send_input({"type": "websocket.receive", "text": json.dumps(frame())})
        assert (await producer.receive_output(timeout=5))["code"] == 4401
        foreign = socket(path, [(b"cookie", cookie), (b"origin", b"https://foreign.example")])
        await foreign.send_input({"type": "websocket.connect"})
        assert (await foreign.receive_output(timeout=5))["type"] == "websocket.close"
        await disconnect(foreign)
        await disconnect(producer)
        await disconnect(viewer)
    asyncio.run(run())


@pytest.mark.django_db(transaction=True)
@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}, ALLOWED_HOSTS=["testserver"])
def test_anonymous_view_and_bad_station_token_are_denied(nomenclature):
    async def run():
        for path, headers in [
            (f"/ws/admin/nomenclatures/{nomenclature.pk}/runtime/", [(b"origin", b"http://testserver")]),
            ("/ws/station/v2/runtime/", [(b"authorization", b"Station invalid")]),
        ]:
            peer = socket(path, headers)
            await peer.send_input({"type": "websocket.connect"})
            assert (await peer.receive_output(timeout=5))["type"] == "websocket.close"
            await disconnect(peer)
    asyncio.run(run())
