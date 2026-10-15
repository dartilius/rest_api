"""Преобразование и проверка публичного запроса единых заказов."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import time

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from orders.unified_models import validate_order_weekdays


ORDER_TYPES = {"bg": "background", "ad": "advertising"}
ADVERTISING_POLICIES = {
    "continuous",
    "workday",
    "hourly_slots",
    "fixed_time",
    "open_offset",
    "close_offset",
    "open_to_fixed",
    "fixed_to_close",
    "start_to_close",
    "event",
}
BROADCAST_TYPE_TO_POLICY = {
    0: "workday",
    1: "open_offset",
    2: "close_offset",
    3: "fixed_time",
    4: "open_to_fixed",
    5: "fixed_to_close",
    6: "event",
    7: "continuous",
}
REQUIRED_PARAMETERS_BY_POLICY = {
    "open_offset": ("timedelta",),
    "close_offset": ("timedelta",),
    "fixed_time": ("start_time", "end_time"),
    "open_to_fixed": ("end_time",),
    "fixed_to_close": ("start_time",),
    "start_to_close": ("start_time",),
    "event": ("event", "active_ad"),
}
MIN_TIMES_IN_HOUR = 1
MAX_TIMES_IN_HOUR = 60
TIME_VALUE_PATTERN = re.compile(r"^\d{2}:\d{2}:\d{2}$")


def normalize_public_order_input(data: Mapping, *, creating: bool, current_placement=None) -> dict:
    """Преобразуем публичный запрос в поля модели; общая валидация работает отдельно."""
    if not isinstance(data, Mapping):
        raise serializers.ValidationError({"non_field_errors": "Ожидается JSON-объект заказа с массивом clients."})
    payload = dict(data)
    if not creating and "clients" in payload:
        raise serializers.ValidationError({
            "clients": "Точки существующего заказа нельзя менять; создайте новый заказ."
        })
    parameters = payload.get("parameters")
    if isinstance(parameters, Mapping) and "schedule_mode" in parameters:
        raise serializers.ValidationError({
            "parameters": "Выберите расписание через broadcast_type и соответствующие параметры времени."
        })
    forbidden = set(payload) & {"client", "placement", "nomenclature", "playback_policy", "starts_at", "ends_at"}
    if forbidden:
        raise serializers.ValidationError({
            field: "Это поле не входит в формат запроса заказа."
            for field in sorted(forbidden)
        })
    _normalize_type(payload)
    _normalize_broadcast_interval(payload)
    _normalize_broadcast_type(payload, current_placement=current_placement)

    if creating and "placement" not in payload:
        raise serializers.ValidationError({"type": "Укажите type: bg или ad."})
    if creating and "clients" not in payload:
        raise serializers.ValidationError({"clients": "Укажите непустой список UUID номенклатур."})
    return payload


def _normalize_type(payload: dict) -> None:
    if "type" not in payload:
        return
    order_type = payload.pop("type")
    if type(order_type) is not str or order_type not in ORDER_TYPES:
        raise serializers.ValidationError({"type": "Допустимы только bg и ad."})
    payload["placement"] = ORDER_TYPES[order_type]


def _normalize_broadcast_interval(payload: dict) -> None:
    if "broadcast_interval" not in payload:
        return
    interval = payload.pop("broadcast_interval")
    if not isinstance(interval, Mapping):
        raise serializers.ValidationError({
            "broadcast_interval": "Ожидается объект с полями lower и upper."
        })
    extra = set(interval) - {"lower", "upper"}
    missing = {"lower", "upper"} - set(interval)
    if extra or missing:
        raise serializers.ValidationError({
            "broadcast_interval": (
                "Для точного преобразования передайте только lower и upper."
            )
        })
    payload["starts_at"] = interval["lower"]
    payload["ends_at"] = interval["upper"]


def _normalize_broadcast_type(payload: dict, *, current_placement=None) -> None:
    if "broadcast_type" not in payload:
        return
    raw_value = payload.pop("broadcast_type")
    if type(raw_value) is int:
        broadcast_type = raw_value
    elif isinstance(raw_value, str) and re.fullmatch(r"[0-7]", raw_value):
        broadcast_type = int(raw_value)
    else:
        broadcast_type = None
    if broadcast_type not in BROADCAST_TYPE_TO_POLICY:
        raise serializers.ValidationError({
            "broadcast_type": "Допустимы целые значения от 0 до 7."
        })
    placement = payload.get("placement", current_placement)
    if placement != "advertising":
        raise serializers.ValidationError({
            "broadcast_type": "broadcast_type относится только к рекламному заказу."
        })

    policy = BROADCAST_TYPE_TO_POLICY[broadcast_type]
    payload["playback_policy"] = policy


def validate_unified_order_attributes(attrs: dict, *, instance=None) -> dict:
    """Проверяем подготовленные поля без записи в базу."""
    if instance is not None:
        _validate_immutable_fields(attrs, instance)

    placement = attrs.get("placement", getattr(instance, "placement", None))
    policy = attrs.get("playback_policy", getattr(instance, "playback_policy", "workday"))
    starts_at = attrs.get("starts_at", getattr(instance, "starts_at", None))
    ends_at = attrs.get("ends_at", getattr(instance, "ends_at", None))
    is_permanent = attrs.get("is_permanent", getattr(instance, "is_permanent", False))
    parameters = attrs.get("parameters", getattr(instance, "parameters", {}) or {})
    nomenclature = attrs.get("nomenclature", getattr(instance, "nomenclature", None))

    parameters = _validate_common_parameters(
        parameters,
        is_permanent=is_permanent,
        playback_policy=policy,
    )
    if parameters is not attrs.get("parameters"):
        attrs["parameters"] = parameters
    _validate_period(
        attrs,
        placement=placement,
        starts_at=starts_at,
        ends_at=ends_at,
        is_permanent=is_permanent,
    )
    _validate_placement_policy(placement, policy, is_permanent)
    if placement == "advertising":
        attrs["parameters"] = _validate_advertising_schedule(
            attrs,
            policy=policy,
            parameters=parameters,
            nomenclature=nomenclature,
            starts_at=starts_at,
            ends_at=ends_at,
        )
    return attrs


def _validate_immutable_fields(attrs: dict, instance) -> None:
    for field in ("nomenclature", "placement"):
        if field in attrs and attrs[field] != getattr(instance, field):
            raise serializers.ValidationError({
                field: "Для смены точки или размещения отмените старый заказ и создайте новый."
            })


def _validate_common_parameters(parameters, *, is_permanent: bool, playback_policy: str) -> dict:
    if not isinstance(parameters, dict):
        raise serializers.ValidationError({"parameters": "Параметры должны быть JSON-объектом."})
    try:
        validate_order_weekdays(
            parameters,
            is_permanent=is_permanent,
            playback_policy=playback_policy,
        )
    except DjangoValidationError as exc:
        raise serializers.ValidationError(exc.message_dict) from exc

    normalized = parameters
    if "weekdays" in parameters and set(parameters["weekdays"]) == set(range(7)):
        normalized = dict(parameters)
        normalized.pop("weekdays")

    weight = normalized.get("weight", 50)
    if isinstance(weight, bool) or not isinstance(weight, int) or not 0 <= weight <= 100:
        raise serializers.ValidationError({
            "parameters": "weight должен быть целым числом от 0 до 100."
        })
    if "audio_muted" in normalized and not isinstance(normalized["audio_muted"], bool):
        raise serializers.ValidationError({
            "parameters": "audio_muted должен быть true или false."
        })
    if "image_duration_seconds" in normalized:
        duration = normalized["image_duration_seconds"]
        if type(duration) is not int or not 1 <= duration <= 86400:
            raise serializers.ValidationError({
                "parameters": "image_duration_seconds должен быть целым числом от 1 до 86400."
            })
    return normalized


def _validate_period(attrs, *, placement, starts_at, ends_at, is_permanent) -> None:
    if placement == "background" and is_permanent and "ends_at" not in attrs:
        ends_at = None
        attrs["ends_at"] = None
    if starts_at and ends_at and starts_at >= ends_at:
        raise serializers.ValidationError({"ends_at": "Окончание должно быть позднее начала."})
    if is_permanent and ends_at is not None:
        raise serializers.ValidationError({
            "ends_at": "У бессрочного заказа не может быть окончания."
        })


def _validate_placement_policy(placement, policy, is_permanent) -> None:
    if placement == "advertising" and is_permanent:
        raise serializers.ValidationError({
            "is_permanent": "Бессрочным может быть только фоновый заказ."
        })
    if placement == "advertising" and policy not in ADVERTISING_POLICIES:
        raise serializers.ValidationError({
            "playback_policy": "Это правило недоступно для рекламы."
        })
    if placement == "background" and policy != "workday":
        raise serializers.ValidationError({
            "playback_policy": "Для фонового заказа сейчас доступно только workday."
        })


def _validate_advertising_schedule(
    attrs,
    *,
    policy,
    parameters,
    nomenclature,
    starts_at,
    ends_at,
) -> dict:
    normalized = dict(parameters)
    if policy == "continuous":
        normalized.pop("times_in_hour", None)
        attrs["suppress_background_audio"] = not normalized.get("audio_muted", False)
        attrs["suppress_background_visual"] = True
    else:
        normalized["times_in_hour"] = _validate_frequency(normalized)

    missing = [
        key for key in REQUIRED_PARAMETERS_BY_POLICY.get(policy, ())
        if not normalized.get(key)
    ]
    if missing:
        raise serializers.ValidationError({
            "parameters": f"Для выбранного расписания обязательны: {', '.join(missing)}."
        })
    for key in ("timedelta", "start_time", "end_time"):
        if key in normalized:
            _validate_clock_value(normalized, key)
    if policy == "start_to_close":
        validate_start_time_in_workday(normalized["start_time"], nomenclature)
    if policy == "fixed_time" and normalized["start_time"] >= normalized["end_time"]:
        raise serializers.ValidationError({
            "parameters": "start_time должен быть раньше end_time."
        })

    missing_dates = {
        field: "Для рекламного заказа укажите начало и окончание периода."
        for field, value in (("starts_at", starts_at), ("ends_at", ends_at))
        if value is None
    }
    if missing_dates:
        raise serializers.ValidationError(missing_dates)
    return normalized


def _validate_frequency(parameters: dict) -> int:
    try:
        raw_times = parameters["times_in_hour"]
        if isinstance(raw_times, bool) or not isinstance(raw_times, (int, str)):
            raise ValueError("times_in_hour must be an integer")
        times_in_hour = int(raw_times)
    except (KeyError, TypeError, ValueError) as exc:
        raise serializers.ValidationError({
            "parameters": "Для рекламы обязателен times_in_hour: целое число от 1 до 60."
        }) from exc
    if not MIN_TIMES_IN_HOUR <= times_in_hour <= MAX_TIMES_IN_HOUR:
        raise serializers.ValidationError({
            "parameters": "times_in_hour может быть только целым числом от 1 до 60."
        })
    return times_in_hour


def _validate_clock_value(parameters: dict, key: str) -> None:
    value = parameters.get(key)
    if not isinstance(value, str) or not TIME_VALUE_PATTERN.fullmatch(value):
        raise serializers.ValidationError({
            "parameters": f"{key} должен иметь формат HH:MM:SS, например 09:30:00."
        })
    hours, minutes, seconds = (int(part) for part in value.split(":"))
    if minutes > 59 or seconds > 59 or (key != "timedelta" and hours > 23):
        raise serializers.ValidationError({
            "parameters": f"{key} содержит недопустимое время: {value}."
        })


def validate_start_time_in_workday(start_time: str, nomenclature) -> None:
    """Проверяем, что первый рекламный выход попадает в рабочее время точки."""
    worktime_start = getattr(nomenclature, "worktime_start", None)
    worktime_end = getattr(nomenclature, "worktime_end", None)
    if worktime_start is None or worktime_end is None:
        return

    first_run = time.fromisoformat(start_time)
    if worktime_start < worktime_end:
        is_in_workday = worktime_start <= first_run < worktime_end
    else:
        is_in_workday = first_run >= worktime_start or first_run < worktime_end
    if not is_in_workday:
        raise serializers.ValidationError({
            "parameters": "Первый выход должен быть в рабочее время точки."
        })


def validate_prepared_orders(orders) -> None:
    """Проверяем все точки до записи первого заказа в транзакции."""
    from orders.services.unified_order_delivery import validate_order_delivery

    for order in orders:
        if order.playback_policy == "start_to_close":
            validate_start_time_in_workday(
                order.parameters["start_time"],
                order.nomenclature,
            )
        try:
            order.full_clean()
            validate_order_delivery(order)
        except DjangoValidationError as exc:
            detail = exc.message_dict if hasattr(exc, "message_dict") else {"detail": exc.messages}
            raise serializers.ValidationError(detail) from exc
