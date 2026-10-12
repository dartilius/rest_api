"""Playback labels and time units are readable without exposing transport data."""

from types import SimpleNamespace

import pytest
from django.contrib.admin.sites import site

from nomenclatures.player_v2.runtime.presentation import broadcast_context, human_duration
from nomenclatures.models import Nomenclature


@pytest.mark.parametrize("value,expected", [
    (0, "0 сек"), (500, "Менее секунды"), (1000, "1 сек"),
    (59000, "59 сек"), (60000, "1 мин"), (93000, "1 мин 33 сек"),
    (3600000, "1 ч"), (3661000, "1 ч 1 мин 1 сек"),
    (None, "Не определена"), (True, "Не определена"), (-1, "Не определена"),
    ("93000", "Не определена"), (float("nan"), "Не определена"), (float("inf"), "Не определена"),
])
def test_time_units(value, expected):
    assert human_duration(value) == expected


@pytest.mark.parametrize("duration_field", ["duration_ms", "duration_seconds"])
def test_advertisement_milliseconds_and_legacy_mislabeled_field_are_readable(duration_field):
    context = broadcast_context({"mode": "ad", "current_ad": {
        "name": "Рекламный ролик", "type": "VIDEO", duration_field: 93000,
    }})
    assert context["mode"] == "Реклама"
    assert context["advertisement"]["duration"] == "1 мин 33 сек"
    assert context["advertisement"]["type"] == "Видеореклама"


def test_background_ms_and_pause_are_localized():
    context = broadcast_context({"mode": "music", "maintenance_mode": False, "background": [
        {"name": "Музыка", "type": 0, "status": "играет", "duration": 93000, "position": 12000},
        {"name": "Фото", "type": 2, "status": "пауза", "duration": 5000, "position": 0},
    ]})
    assert context["mode"] == "Фоновый контент"
    assert context["background"][0]["position"] == "12 сек"
    assert context["background"][0]["duration"] == "1 мин 33 сек"
    assert context["background"][1]["type"] == "Изображение"
    assert context["background"][1]["status"] == "На паузе"


@pytest.mark.parametrize("runtime", [None, [], "invalid", {"mode": [], "background": [False, "invalid"]}])
def test_missing_or_bad_snapshot_is_safe(runtime):
    context = broadcast_context(runtime)
    assert context["mode"] == "Режим не определён"
    assert context["background"] == []


def test_template_escapes_content_and_hides_protocol_settings_and_ids():
    obj = SimpleNamespace(runtime_state={
        "mode": "maintenance", "maintenance_mode": True,
        "background": [{"type": 1, "name": '<img src=x onerror="alert(1)">',
                        "status": "paused", "duration_ms": 93000, "position_ms": 3000,
                        "order_id": "hidden-uuid"}],
        "applied_settings": {"mon": {"default_volume": [71]}},
        "station_protocol": {"unified_orders_version": 1},
    })
    html = str(site._registry[Nomenclature].current_broadcast_state(obj))
    assert "Сервисный режим" in html
    assert "Включён" in html
    assert "На паузе" in html
    assert "1 мин 33 сек" in html
    assert "<img src=x" not in html
    assert "&lt;img" in html
    assert "hidden-uuid" not in html
    assert "default_volume" not in html
    assert "unified_orders_version" not in html
