"""Ordering, isolation, persistence budget and the reserve transport."""

from contextlib import nullcontext
from copy import deepcopy
from datetime import timedelta
from uuid import uuid4

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from nomenclatures.models import StationCredential, StationRuntimeSnapshot
from nomenclatures.player_v2.credentials import hash_station_token
from nomenclatures.player_v2.runtime import service as runtime_live
from nomenclatures.player_v2.runtime.serializers import RuntimeSnapshotSerializer
from nomenclatures.player_v2.runtime.service import (
    accept_runtime,
    display_snapshot,
    publish_legacy_runtime,
)


class Cache:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return deepcopy(self.values.get(key))

    def set(self, key, value, **kwargs):
        self.values[key] = deepcopy(value)

    def lock(self, key, **kwargs):
        return nullcontext()


@pytest.fixture
def runtime_cache(monkeypatch):
    fake = Cache()
    monkeypatch.setattr(runtime_live, "cache", fake)
    monkeypatch.setattr(runtime_live, "_broadcast", lambda station_id: None)
    return fake


@pytest.fixture
def credential(nomenclature):
    return StationCredential.objects.create(nomenclature=nomenclature, token_hash=hash_station_token("runtime-test-token"))


def frame(*, stream=None, sequence=1, name="Видео", position=0):
    return {"stream_id": str(stream or uuid4()), "sequence": sequence, "state": {
        "mode": "music", "maintenance_mode": False, "current_ad": None,
        "background": [{"name": name, "type": 1, "status": "играет", "duration_ms": 93000, "position_ms": position}],
    }}


@pytest.mark.django_db
def test_late_sequence_and_retired_stream_cannot_replace_new_content(credential, runtime_cache):
    first = frame(sequence=2, name="Текущий")
    assert accept_runtime(credential, first, transport="websocket")["accepted"]
    older = {**first, "sequence": 1, "state": frame(name="Устаревший")["state"]}
    assert not accept_runtime(credential, older, transport="polling")["accepted"]
    restarted = frame(name="После перезапуска")
    assert accept_runtime(credential, restarted, transport="websocket")["accepted"]
    assert not accept_runtime(credential, {**first, "sequence": 3}, transport="polling")["accepted"]
    content = display_snapshot(credential.nomenclature_id)["content"]
    assert content["background"][0]["name"] == "После перезапуска"


@pytest.mark.django_db
def test_progress_does_not_write_postgresql_until_checkpoint(credential, runtime_cache, monkeypatch):
    now = timezone.now()
    monkeypatch.setattr(runtime_live.timezone, "now", lambda: now)
    current = frame()
    accept_runtime(credential, current, transport="websocket")
    now += timedelta(seconds=5)
    with CaptureQueriesContext(connection) as queries:
        accept_runtime(credential, {**current, "sequence": 2, "state": frame(position=5000)["state"]}, transport="websocket")
    assert not any('UPDATE "station_runtime_snapshot"' in query["sql"] for query in queries)
    assert StationRuntimeSnapshot.objects.get(pk=credential.nomenclature_id).state["background"][0]["position_ms"] == 0
    now += timedelta(seconds=30)
    accept_runtime(credential, {**current, "sequence": 3, "state": frame(position=35000)["state"]}, transport="websocket")
    assert StationRuntimeSnapshot.objects.get(pk=credential.nomenclature_id).state["background"][0]["position_ms"] == 35000


@pytest.mark.django_db
def test_cache_failure_uses_postgresql_reserve_and_still_orders_frames(credential, runtime_cache, monkeypatch):
    def fail(*args, **kwargs):
        raise ConnectionError("Redis unavailable")
    monkeypatch.setattr(runtime_cache, "lock", fail)
    current = frame(sequence=2)
    assert accept_runtime(credential, current, transport="polling")["accepted"]
    assert not accept_runtime(credential, {**current, "sequence": 1}, transport="polling")["accepted"]
    assert StationRuntimeSnapshot.objects.get(pk=credential.nomenclature_id).transport == "polling"


@pytest.mark.django_db
def test_revocation_and_other_station_are_isolated(credential, nomenclature_1, runtime_cache):
    current = frame()
    accept_runtime(credential, current, transport="websocket")
    assert not StationRuntimeSnapshot.objects.filter(pk=nomenclature_1.pk).exists()
    credential.is_active = False
    credential.save(update_fields=["is_active"])
    assert accept_runtime(credential, frame(), transport="websocket")["code"] == "credential_revoked"


@pytest.mark.django_db
def test_legacy_cannot_replace_a_fresh_v2_snapshot(credential, runtime_cache):
    accept_runtime(credential, frame(name="Новый Player"), transport="websocket")
    publish_legacy_runtime(credential.nomenclature_id, {"mode": "music", "maintenance_mode": False,
        "background": [{"name": "Legacy", "type": 1, "duration": 10000, "position": 0}]})
    assert display_snapshot(credential.nomenclature_id)["content"]["background"][0]["name"] == "Новый Player"


@pytest.mark.parametrize("change", [
    {"sequence": True}, {"sequence": 1.5}, {"sequence": 0},
    {"state": {"mode": "music", "maintenance_mode": False, "settings": {}}},
])
def test_bad_frames_or_settings_are_rejected(change):
    serializer = RuntimeSnapshotSerializer(data={**frame(), **change})
    assert not serializer.is_valid()


@pytest.mark.django_db(transaction=True)
def test_http_snapshot_is_the_reserve_and_requires_the_station_token(client, credential, runtime_cache):
    current = frame(name="HTTP reserve")
    response = client.post("/api/station/v2/sync/", data={"runtime_snapshot": current},
        content_type="application/json", HTTP_AUTHORIZATION="Station runtime-test-token")
    assert response.status_code == 200
    assert response.json()["runtime_snapshot_received"]["accepted"] is True
    assert display_snapshot(credential.nomenclature_id)["content"]["background"][0]["name"] == "HTTP reserve"
    unauthorized = client.post("/api/station/v2/sync/", data={"runtime_snapshot": frame()}, content_type="application/json")
    assert unauthorized.status_code == 401


@pytest.mark.django_db
def test_admin_polling_endpoint_has_the_same_view_permissions(client, super_user, user, credential, runtime_cache):
    from django.urls import reverse
    accept_runtime(credential, frame(name="Live"), transport="websocket")
    url = reverse("admin:nomenclature_runtime_state", args=[credential.nomenclature_id])
    client.force_login(super_user)
    response = client.get(url)
    assert response.status_code == 200
    assert response.json()["content"]["background"][0]["name"] == "Live"
    client.force_login(user)
    assert client.get(url).status_code in (302, 403)
