"""Pure, legacy-compatible partial updates for station volume settings."""

from __future__ import annotations

from copy import deepcopy
from datetime import time
import re
from typing import Any


DAYS_OF_WEEK = frozenset({"mon", "tue", "wed", "thu", "fri", "sat", "sun"})
VOLUME_INDEXES = {
    ("background", "left"): 0,
    ("advertisement", "left"): 1,
    ("background", "right"): 2,
    ("advertisement", "right"): 3,
}
BACKGROUND_BOOLEAN_FIELDS = frozenset(
    {
        "video_enabled",
        "video_muted",
        "img_enabled",
        "music_random",
        "video_random",
        "img_random",
    }
)
BACKGROUND_INTEGER_RANGES = {"img_duration": (1, 60)}
MAX_OPERATIONS = 256
INTERVAL_PATTERN = re.compile(r"^(\d{2}:\d{2}:\d{2})-(\d{2}:\d{2}:\d{2})$")


class SettingsPatchError(ValueError):
    """The requested partial settings update is invalid."""


def validate_settings_document(settings: dict[str, Any]) -> None:
    """Проверяет полный документ настроек без его изменения."""
    _validate_settings(settings)


def apply_settings_operations(
    current_settings: dict[str, Any], operations: list[dict[str, Any]]
) -> dict[str, Any]:
    """Применяет разрешённые точечные изменения без изменения исходных настроек.

    Paths are a small, deliberate JSON-Pointer subset.  ``/days`` is a
    virtual prefix: the stored format remains the legacy ``mon`` .. ``sun``
    top-level mapping.  The legacy volume order is preserved as
    ``[background_left, advertisement_left, background_right,
    advertisement_right]``.
    """

    _validate_settings(current_settings)

    if not isinstance(operations, list) or not operations:
        raise SettingsPatchError("operations must be a non-empty list")
    if len(operations) > MAX_OPERATIONS:
        raise SettingsPatchError(f"operations may contain at most {MAX_OPERATIONS} items")

    merged = deepcopy(current_settings)
    for operation in operations:
        _apply_operation(merged, operation)

    _validate_settings(merged)
    return merged


def _apply_operation(settings: dict[str, Any], operation: dict[str, Any]) -> None:
    if not isinstance(operation, dict):
        raise SettingsPatchError("each operation must be an object")

    op = operation.get("op")
    path = operation.get("path")
    if not isinstance(op, str) or op not in {"set", "remove"}:
        raise SettingsPatchError("operation op must be 'set' or 'remove'")
    if not isinstance(path, str):
        raise SettingsPatchError("operation path must be a string")

    expected_keys = {"op", "path", "value"} if op == "set" else {"op", "path"}
    if set(operation) != expected_keys:
        raise SettingsPatchError("operation contains unsupported fields")

    parts = _parse_pointer(path)
    if len(parts) < 3 or parts[:1] != ["days"]:
        raise SettingsPatchError("path must start with /days/{day}")

    day = parts[1]
    if day not in DAYS_OF_WEEK:
        raise SettingsPatchError(f"unknown day {day!r}")

    day_settings = settings[day]
    if parts[2] == "worktime":
        _apply_worktime_operation(day_settings, parts[3:], op, operation.get("value"))
        return

    if parts[2] == "default_volume":
        _apply_default_volume_operation(day_settings, parts[3:], op, operation.get("value"))
        return

    if parts[2] == "custom_volume":
        _apply_custom_volume_operation(day_settings, parts[3:], op, operation.get("value"))
        return

    if parts[2] == "background":
        _apply_background_operation(day_settings, parts[3:], op, operation.get("value"))
        return

    raise SettingsPatchError(
        "поддерживаются только пути worktime, default_volume, custom_volume и background"
    )


def _apply_worktime_operation(
    day_settings: dict[str, Any], parts: list[str], op: str, value: Any
) -> None:
    """Меняет только рабочее время выбранного дня."""
    if op != "set" or parts:
        raise SettingsPatchError("worktime поддерживает только установку одного интервала")
    _parse_interval(value)
    day_settings["worktime"] = value


def _apply_background_operation(
    day_settings: dict[str, Any], parts: list[str], op: str, value: Any
) -> None:
    """Меняет один параметр фона, сохраняя остальные параметры дня."""
    if op != "set" or len(parts) != 1:
        raise SettingsPatchError("background поддерживает только установку одного параметра")

    field = parts[0]
    if field in BACKGROUND_BOOLEAN_FIELDS:
        if not isinstance(value, bool):
            raise SettingsPatchError(f"{field} должен быть логическим значением")
        day_settings[field] = value
        return

    value_range = BACKGROUND_INTEGER_RANGES.get(field)
    if value_range is None:
        raise SettingsPatchError(f"неподдерживаемый параметр фона {field!r}")
    if not isinstance(value, int) or isinstance(value, bool):
        raise SettingsPatchError(f"{field} должен быть целым числом")
    minimum, maximum = value_range
    if not minimum <= value <= maximum:
        raise SettingsPatchError(f"{field} должен быть от {minimum} до {maximum}")
    day_settings[field] = value


def _apply_default_volume_operation(
    day_settings: dict[str, Any], parts: list[str], op: str, value: Any
) -> None:
    if op != "set" or len(parts) != 2:
        raise SettingsPatchError("default_volume only supports setting one channel")

    index = _volume_index(parts[0], parts[1])
    day_settings["default_volume"][index] = _validate_volume_value(value)


def _apply_custom_volume_operation(
    day_settings: dict[str, Any], parts: list[str], op: str, value: Any
) -> None:
    if not parts:
        raise SettingsPatchError("custom_volume path must include an interval")

    interval = parts[0]
    _parse_interval(interval)
    custom_volume = day_settings.setdefault("custom_volume", {})
    if not isinstance(custom_volume, dict):
        raise SettingsPatchError("custom_volume must be an object")

    if len(parts) == 1:
        if op == "remove":
            if interval not in custom_volume:
                raise SettingsPatchError(f"custom volume interval {interval!r} does not exist")
            del custom_volume[interval]
            return
        custom_volume[interval] = _named_volume_to_legacy(value)
        return

    if op != "set" or len(parts) != 3:
        raise SettingsPatchError("custom_volume channel paths only support set")
    if interval not in custom_volume:
        raise SettingsPatchError(
            "create a custom_volume interval with its full four-channel value first"
        )

    index = _volume_index(parts[1], parts[2])
    custom_volume[interval][index] = _validate_volume_value(value)


def _parse_pointer(path: str) -> list[str]:
    if not path.startswith("/") or path == "/":
        raise SettingsPatchError("path must be a non-empty JSON Pointer")
    return [_decode_pointer_segment(segment) for segment in path.split("/")[1:]]


def _decode_pointer_segment(segment: str) -> str:
    decoded: list[str] = []
    position = 0
    while position < len(segment):
        char = segment[position]
        if char != "~":
            decoded.append(char)
            position += 1
            continue
        if position + 1 >= len(segment) or segment[position + 1] not in {"0", "1"}:
            raise SettingsPatchError("path contains an invalid JSON Pointer escape")
        decoded.append("~" if segment[position + 1] == "0" else "/")
        position += 2
    return "".join(decoded)


def _volume_index(source: str, channel: str) -> int:
    try:
        return VOLUME_INDEXES[(source, channel)]
    except KeyError as exc:
        raise SettingsPatchError(
            "volume path must name background or advertisement and left or right"
        ) from exc


def _named_volume_to_legacy(value: Any) -> list[int]:
    if not isinstance(value, dict) or set(value) != {"background", "advertisement"}:
        raise SettingsPatchError("whole interval value must contain background and advertisement")

    values: dict[tuple[str, str], int] = {}
    for source in ("background", "advertisement"):
        channels = value[source]
        if not isinstance(channels, dict) or set(channels) != {"left", "right"}:
            raise SettingsPatchError(f"{source} must contain left and right")
        for channel in ("left", "right"):
            values[(source, channel)] = _validate_volume_value(channels[channel])

    return [
        values[("background", "left")],
        values[("advertisement", "left")],
        values[("background", "right")],
        values[("advertisement", "right")],
    ]


def _validate_settings(settings: Any) -> None:
    if not isinstance(settings, dict) or not DAYS_OF_WEEK.issubset(settings):
        raise SettingsPatchError("settings must contain mon through sun")

    for day in DAYS_OF_WEEK:
        day_settings = settings[day]
        if not isinstance(day_settings, dict):
            raise SettingsPatchError(f"settings for {day!r} must be an object")
        if "worktime" not in day_settings or "default_volume" not in day_settings:
            raise SettingsPatchError(f"settings for {day!r} require worktime and default_volume")
        _parse_interval(day_settings["worktime"])
        _validate_legacy_volume(day_settings["default_volume"])
        _validate_custom_volume(day_settings.get("custom_volume", {}))


def _validate_custom_volume(custom_volume: Any) -> None:
    if not isinstance(custom_volume, dict):
        raise SettingsPatchError("custom_volume must be an object")

    intervals: list[tuple[time, time, str]] = []
    for interval, volume in custom_volume.items():
        start, end = _parse_interval(interval)
        _validate_legacy_volume(volume)
        intervals.append((start, end, interval))

    for (_, current_end, _), (next_start, _, _) in zip(
        sorted(intervals), sorted(intervals)[1:]
    ):
        if current_end > next_start:
            raise SettingsPatchError("custom_volume intervals must not overlap")


def _parse_interval(value: Any) -> tuple[time, time]:
    if not isinstance(value, str):
        raise SettingsPatchError("interval must be a string")
    match = INTERVAL_PATTERN.fullmatch(value)
    if match is None:
        raise SettingsPatchError("interval must have the form HH:MM:SS-HH:MM:SS")
    try:
        start = time.fromisoformat(match.group(1))
        end = time.fromisoformat(match.group(2))
    except ValueError as exc:
        raise SettingsPatchError("interval contains an invalid clock time") from exc
    if not start < end:
        raise SettingsPatchError("interval start must be earlier than its end")
    return start, end


def _validate_legacy_volume(value: Any) -> None:
    if not isinstance(value, list) or len(value) != 4:
        raise SettingsPatchError("volume must be a four-item list")
    for channel in value:
        _validate_volume_value(channel)


def _validate_volume_value(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 100:
        raise SettingsPatchError("volume must be an integer from 0 through 100")
    return value
