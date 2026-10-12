"""Contracts for pure, legacy-compatible station settings updates."""

from copy import deepcopy

import pytest

from nomenclatures.player_v2.settings import SettingsPatchError, apply_settings_operations


def _settings() -> dict:
    settings = {
        day: {
            "worktime": "09:00:00-20:00:00",
            "default_volume": [10, 20, 30, 40],
            "custom_volume": {"10:00:00-12:00:00": [11, 22, 33, 44]},
            "future_option": {"preserve": True},
        }
        for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
    }
    settings["wed"]["custom_volume"] = {
        "10:00:00-12:00:00": [11, 22, 33, 44],
        "14:00:00-16:00:00": [55, 66, 77, 88],
    }
    settings.update(
        {
            "audio_device": "device-42",
            "maintenance_mode": False,
            "dark_mode": True,
        }
    )
    return settings


def test_default_volume_channel_update_preserves_unaddressed_settings() -> None:
    current = _settings()

    merged = apply_settings_operations(
        current,
        [
            {
                "op": "set",
                "path": "/days/tue/default_volume/background/left",
                "value": 91,
            }
        ],
    )

    assert merged["tue"]["default_volume"] == [91, 20, 30, 40]
    assert merged["mon"] == current["mon"]
    assert merged["tue"]["custom_volume"] == current["tue"]["custom_volume"]
    assert merged["tue"]["future_option"] == {"preserve": True}
    assert merged["audio_device"] == "device-42"
    assert merged["maintenance_mode"] is False
    assert merged["dark_mode"] is True
    assert current["tue"]["default_volume"] == [10, 20, 30, 40]


def test_background_settings_change_only_addressed_fields() -> None:
    current = _settings()
    current["mon"].update(
        {
            "video_enabled": True,
            "video_muted": True,
            "img_enabled": True,
            "img_duration": 5,
            "music_random": True,
            "video_random": True,
            "img_random": True,
        }
    )

    merged = apply_settings_operations(
        current,
        [
            {"op": "set", "path": "/days/mon/background/video_enabled", "value": False},
            {"op": "set", "path": "/days/mon/background/img_duration", "value": 12},
        ],
    )

    assert merged["mon"]["video_enabled"] is False
    assert merged["mon"]["img_duration"] == 12
    assert merged["mon"]["video_muted"] is True
    assert merged["mon"]["default_volume"] == current["mon"]["default_volume"]
    assert merged["tue"] == current["tue"]
    assert current["mon"]["video_enabled"] is True


def test_worktime_change_preserves_channels_and_background_settings():
    current = _settings()
    current["thu"]["video_enabled"] = True

    merged = apply_settings_operations(
        current,
        [{"op": "set", "path": "/days/thu/worktime", "value": "10:00:00-22:00:00"}],
    )

    assert merged["thu"]["worktime"] == "10:00:00-22:00:00"
    assert merged["thu"]["default_volume"] == current["thu"]["default_volume"]
    assert merged["thu"]["video_enabled"] is True
    assert merged["fri"] == current["fri"]


@pytest.mark.parametrize(
    ("path", "value"),
    [
        ("/days/mon/background/video_enabled", 1),
        ("/days/mon/background/img_duration", True),
        ("/days/mon/background/img_duration", 61),
        ("/days/mon/background/unknown", False),
    ],
)
def test_invalid_background_setting_does_not_mutate_settings(path, value):
    current = _settings()
    before = deepcopy(current)

    with pytest.raises(SettingsPatchError):
        apply_settings_operations(current, [{"op": "set", "path": path, "value": value}])

    assert current == before


def test_custom_volume_channel_update_uses_legacy_channel_order() -> None:
    merged = apply_settings_operations(
        _settings(),
        [
            {
                "op": "set",
                "path": "/days/wed/custom_volume/10:00:00-12:00:00/advertisement/right",
                "value": 99,
            }
        ],
    )

    assert merged["wed"]["custom_volume"]["10:00:00-12:00:00"] == [11, 22, 33, 99]
    assert merged["wed"]["custom_volume"]["14:00:00-16:00:00"] == [55, 66, 77, 88]


def test_custom_volume_whole_interval_set_and_remove() -> None:
    current = _settings()
    interval = "16:00:00-18:00:00"
    merged = apply_settings_operations(
        current,
        [
            {
                "op": "set",
                "path": f"/days/fri/custom_volume/{interval}",
                "value": {
                    "background": {"left": 1, "right": 3},
                    "advertisement": {"left": 2, "right": 4},
                },
            }
        ],
    )
    assert merged["fri"]["custom_volume"][interval] == [1, 2, 3, 4]

    removed = apply_settings_operations(
        merged,
        [{"op": "remove", "path": f"/days/fri/custom_volume/{interval}"}],
    )
    assert interval not in removed["fri"]["custom_volume"]


def test_invalid_operation_keeps_caller_settings_unchanged() -> None:
    current = _settings()
    before = deepcopy(current)

    with pytest.raises(SettingsPatchError, match="integer from 0 through 100"):
        apply_settings_operations(
            current,
            [
                {
                    "op": "set",
                    "path": "/days/mon/default_volume/background/left",
                    "value": 101,
                }
            ],
        )

    assert current == before


def test_new_custom_interval_cannot_overlap_an_existing_interval() -> None:
    current = _settings()

    with pytest.raises(SettingsPatchError, match="must not overlap"):
        apply_settings_operations(
            current,
            [
                {
                    "op": "set",
                    "path": "/days/mon/custom_volume/11:00:00-13:00:00",
                    "value": {
                        "background": {"left": 1, "right": 3},
                        "advertisement": {"left": 2, "right": 4},
                    },
                }
            ],
        )


@pytest.mark.parametrize(
    "invalid_worktime",
    ["09:00-20:00", "09:00:00.500-20:00:00", "09:00:00+03:00-20:00:00"],
)
def test_settings_reject_non_legacy_interval_formats(invalid_worktime: str) -> None:
    current = _settings()
    current["sun"]["worktime"] = invalid_worktime

    with pytest.raises(SettingsPatchError, match="HH:MM:SS-HH:MM:SS"):
        apply_settings_operations(
            current,
            [
                {
                    "op": "set",
                    "path": "/days/mon/default_volume/background/left",
                    "value": 50,
                }
            ],
        )


def test_operations_limit_and_unhashable_op_are_rejected() -> None:
    operation = {
        "op": "set",
        "path": "/days/mon/default_volume/background/left",
        "value": 50,
    }

    with pytest.raises(SettingsPatchError, match="at most 256"):
        apply_settings_operations(_settings(), [operation] * 257)

    with pytest.raises(SettingsPatchError, match="op must be"):
        apply_settings_operations(
            _settings(),
            [{"op": [], "path": "/days/mon/default_volume/background/left"}],
        )


@pytest.mark.parametrize(
    ("channel", "expected"),
    [
        ("background/left", [91, 20, 30, 40]),
        ("advertisement/left", [10, 91, 30, 40]),
        ("background/right", [10, 20, 91, 40]),
        ("advertisement/right", [10, 20, 30, 91]),
    ],
)
def test_each_named_channel_maps_to_its_legacy_slot(channel, expected):
    result = apply_settings_operations(_settings(), [{
        "op": "set", "path": f"/days/mon/default_volume/{channel}", "value": 91,
    }])
    assert result["mon"]["default_volume"] == expected


def test_copy_one_channel_to_all_days_preserves_other_fields():
    current = _settings()
    expected = deepcopy(current)
    operations = []
    for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun"):
        expected[day]["default_volume"][0] = 73
        operations.append({
            "op": "set", "path": f"/days/{day}/default_volume/background/left",
            "value": 73,
        })
    assert apply_settings_operations(current, operations) == expected


@pytest.mark.parametrize("value", [True, None, -1, 101, 1.5, "50"])
def test_later_invalid_operation_does_not_mutate_any_day(value):
    current = _settings()
    before = deepcopy(current)
    operations = [
        {"op": "set", "path": "/days/mon/default_volume/background/left", "value": 73},
        {"op": "set", "path": "/days/tue/default_volume/advertisement/right", "value": value},
    ]
    with pytest.raises(SettingsPatchError):
        apply_settings_operations(current, operations)
    assert current == before


@pytest.mark.parametrize("path", [
    "/audio_device", "/days/mon", "/days/mon/default_volume",
    "/days/mon/default_volume/background~2/left",
    "/days/mon/default_volume/background~1left",
    "/days/tuesday/default_volume/background/left",
])
def test_paths_outside_volume_allowlist_are_rejected(path):
    with pytest.raises(SettingsPatchError):
        apply_settings_operations(_settings(), [{"op": "set", "path": path, "value": 50}])
