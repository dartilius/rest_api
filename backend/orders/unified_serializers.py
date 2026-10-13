"""REST validation and Swagger field descriptions for unified broadcast orders."""

import re
from datetime import time

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from files.models import Playlist
from nomenclatures.models import Nomenclature
from orders.models import Order


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
MIN_TIMES_IN_HOUR = 1
MAX_TIMES_IN_HOUR = 60
TIME_VALUE_PATTERN = re.compile(r"^\d{2}:\d{2}:\d{2}$")


@extend_schema_field({
    "type": "string",
    "pattern": r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$",
    "example": "2026-09-30 13:04:00",
})
class LocalOrderDateTimeField(serializers.DateTimeField):
    """Keep the local Player timestamp contract identical in JSON and OpenAPI."""

    def __init__(self, **kwargs):
        super().__init__(format="%Y-%m-%d %H:%M:%S", input_formats=("%Y-%m-%d %H:%M:%S",), **kwargs)


def _require_clock_value(parameters, key):
    """Reject ambiguous schedule values before they reach the Player protocol."""
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


def _validate_start_time_in_workday(start_time: str, nomenclature) -> None:
    """Reject a first advertising run outside a configured point workday."""
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


class OrderPlaybackListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        from nomenclatures.player_v2.runtime.service import load_runtime_documents
        rows = list(data.all() if hasattr(data, "all") else data)
        self.context["order_runtime_documents"] = load_runtime_documents(row.nomenclature_id for row in rows)
        return super().to_representation(rows)


class UnifiedOrderSerializer(serializers.ModelSerializer):
    """One order for exactly one Player station."""
    actual_playback = serializers.SerializerMethodField()

    @extend_schema_field({"type": "object", "properties": {
        "code": {"type": "string"}, "label": {"type": "string"},
        "revision": {"type": "integer"}, "error": {"type": "string", "nullable": True},
    }})
    def get_actual_playback(self, obj):
        from orders.services.order_air_state import actual_order_state
        documents = self.context.get("order_runtime_documents")
        if documents is not None:
            return actual_order_state(obj, documents.get(str(obj.nomenclature_id)))
        return actual_order_state(obj)

    delivery = serializers.SerializerMethodField()

    @extend_schema_field({"type": "object", "nullable": True, "properties": {
        "desired_action": {"type": "string"}, "revision": {"type": "integer"},
        "status": {"type": "string"}, "applied_revision": {"type": "integer", "nullable": True},
        "on_air_revision": {"type": "integer", "nullable": True}, "last_error": {"type": "string"},
        "progress": {"type": "object", "nullable": True, "properties": {
            "revision": {"type": "integer"}, "phase": {"type": "string", "enum": ["downloading", "verifying", "applying"]},
            "files_verified": {"type": "integer"}, "files_total": {"type": "integer"},
            "fresh": {"type": "boolean"}, "label": {"type": "string"},
            "received_at": {"type": "string", "example": "2026-10-06 09:00:00"},
        }},
    }})
    def get_delivery(self, obj):
        from orders.models import OrderStationState
        try:
            state = obj.station_state
        except OrderStationState.DoesNotExist:
            return None
        return {"desired_action": state.desired_action, "revision": state.desired_revision,
                "status": state.status, "applied_revision": state.applied_revision,
                "on_air_revision": state.on_air_revision, "last_error": state.last_error,
                "progress": self._delivery_progress(obj)}

    @staticmethod
    def _delivery_progress(obj):
        from orders.services.order_progress import delivery_progress
        return delivery_progress(obj)

    placement = serializers.ChoiceField(
        choices=(
            ("background", "Фоновый контент"),
            ("advertising", "Реклама"),
        ),
        help_text=(
            "background — Player включает фоновую музыку, видео, картинки или ticker из плейлиста; "
            "advertising — отправляет рекламные выходы по заданному правилу."
        ),
    )
    playback_policy = serializers.ChoiceField(
        choices=(
            ("workday", "В рабочее время точки"),
            ("hourly_slots", "Выходы в течение часа"),
            ("open_offset", "От открытия со смещением"),
            ("close_offset", "До закрытия со смещением"),
            ("fixed_time", "В фиксированные часы"),
            ("open_to_fixed", "От открытия до фиксированного часа"),
            ("fixed_to_close", "От фиксированного часа до закрытия"),
            ("start_to_close", "Реклама с указанного времени"),
            ("event", "По событию Player"),
            ("continuous", "Непрерывная реклама вместо фона"),
        ),
        help_text=(
            "Для background сейчас допускается только workday. Для advertising используйте правило "
            "и соответствующие keys в parameters; их назначение и готовые JSON приведены в примерах операции POST."
        ),
    )

    nomenclature = serializers.PrimaryKeyRelatedField(
        queryset=Nomenclature.active.all(),
        help_text="UUID точки вещания. Один запрос создаёт заказ для одной точки.",
    )
    playlist = serializers.PrimaryKeyRelatedField(
        queryset=Playlist.objects.all(),
        help_text="UUID плейлиста. Если есть PlaylistItem, используется его порядок и картинки.",
    )
    created = LocalOrderDateTimeField(read_only=True)
    starts_at = LocalOrderDateTimeField(
        required=False,
        allow_null=True,
        help_text="Локальные дата и время без часового пояса: YYYY-MM-DD HH:MM:SS, например 2026-09-25 09:00:00. Для рекламы обязательно. У фона пусто — начать после доставки заказа Player.",
    )
    ends_at = LocalOrderDateTimeField(
        required=False,
        allow_null=True,
        help_text="Локальные дата и время без часового пояса: YYYY-MM-DD HH:MM:SS. Для рекламы обязательно. Для бессрочного фона можно не передавать или передать null. При переводе в бессрочный фон прежнее окончание очищается, если поле не передано.",
    )
    is_permanent = serializers.BooleanField(
        required=False,
        help_text="true — бессрочный резервный фоновый заказ; допустим только для background и без ends_at.",
    )
    suppress_background_audio = serializers.BooleanField(
        required=False,
        help_text="Для рекламного заказа: true — отключить фоновую музыку. Для continuous определяется автоматически: false при audio_muted=true, иначе true.",
    )
    suppress_background_visual = serializers.BooleanField(
        required=False,
        help_text="Для рекламного заказа: true — скрыть фоновое видео/картинку. Для continuous всегда true.",
    )
    parameters = serializers.JSONField(
        required=False,
        help_text=(
            "Расписание рекламы. Для continuous times_in_hour не нужен и игнорируется; "
            "для остальных правил times_in_hour — целое число выходов за час от 1 до 60; "
            "open_offset/close_offset требуют timedelta, fixed_time — start_time и end_time, "
            "open_to_fixed — end_time, fixed_to_close и start_to_close — start_time; все времена строго HH:MM:SS."
            " audio_muted: true отключает звук рекламного ролика; по умолчанию false. weight — целое число 0–100."
            " Для визуального фона image_duration_seconds — время показа каждой картинки, целое число 1–86400;"
            " без него используется настройка Player."
        ),
    )

    class Meta:
        model = Order
        list_serializer_class = OrderPlaybackListSerializer
        fields = (
            "id", "name", "description", "placement", "playback_policy",
            "nomenclature", "playlist", "starts_at", "ends_at", "is_permanent",
            "suppress_background_audio", "suppress_background_visual", "parameters",
            "status", "revision", "owner", "created", "delivery", "actual_playback",
        )
        read_only_fields = ("id", "owner", "created", "revision", "status")
        extra_kwargs = {
            "parameters": {
                "help_text": "Параметры расписания. Для рекламы, кроме continuous, требуется times_in_hour: целое число от 1 до 60.",
            },
            "status": {
                "help_text": "0 — ожидает эфира, 1 — в эфире, 2 — завершён, 3 — отменён, 4 — ошибка.",
            },
        }

    def validate(self, attrs):
        instance = self.instance
        if instance is not None:
            for field in ("nomenclature", "placement"):
                if field in attrs and attrs[field] != getattr(instance, field):
                    raise serializers.ValidationError({field: "Для смены точки или размещения отмените старый заказ и создайте новый."})
        placement = attrs.get("placement", getattr(instance, "placement", None))
        policy = attrs.get("playback_policy", getattr(instance, "playback_policy", "workday"))
        starts_at = attrs.get("starts_at", getattr(instance, "starts_at", None))
        ends_at = attrs.get("ends_at", getattr(instance, "ends_at", None))
        is_permanent = attrs.get("is_permanent", getattr(instance, "is_permanent", False))
        parameters = attrs.get("parameters", getattr(instance, "parameters", {}) or {})
        nomenclature = attrs.get("nomenclature", getattr(instance, "nomenclature", None))
        if not isinstance(parameters, dict):
            raise serializers.ValidationError({"parameters": "Параметры должны быть JSON-объектом."})
        weight = parameters.get("weight", 50)
        if isinstance(weight, bool) or not isinstance(weight, int) or not 0 <= weight <= 100:
            raise serializers.ValidationError({"parameters": "weight должен быть целым числом от 0 до 100."})
        if "audio_muted" in parameters and not isinstance(parameters["audio_muted"], bool):
            raise serializers.ValidationError({"parameters": "audio_muted должен быть true или false."})
        if "image_duration_seconds" in parameters:
            duration = parameters["image_duration_seconds"]
            if type(duration) is not int or not 1 <= duration <= 86400:
                raise serializers.ValidationError({"parameters": "image_duration_seconds должен быть целым числом от 1 до 86400."})

        if placement == "background" and is_permanent and "ends_at" not in attrs:
            ends_at = None
            attrs["ends_at"] = None

        if starts_at and ends_at and starts_at >= ends_at:
            raise serializers.ValidationError({"ends_at": "Окончание должно быть позднее начала."})
        if is_permanent and ends_at is not None:
            raise serializers.ValidationError({"ends_at": "У бессрочного заказа не может быть окончания."})
        if placement == "advertising" and is_permanent:
            raise serializers.ValidationError({"is_permanent": "Бессрочным может быть только фоновый заказ."})
        if placement == "advertising" and policy not in ADVERTISING_POLICIES:
            raise serializers.ValidationError({"playback_policy": "Это правило недоступно для рекламы."})
        if placement == "background" and policy != "workday":
            raise serializers.ValidationError({
                "playback_policy": "Для фонового заказа сейчас доступно только workday."
            })
        if placement == "advertising":
            parameters = dict(parameters)
            if policy == "continuous":
                parameters.pop("times_in_hour", None)
                attrs["suppress_background_audio"] = not parameters.get("audio_muted", False)
                attrs["suppress_background_visual"] = True
            else:
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
                parameters["times_in_hour"] = times_in_hour
            required_by_policy = {
                "open_offset": ("timedelta",),
                "close_offset": ("timedelta",),
                "fixed_time": ("start_time", "end_time"),
                "open_to_fixed": ("end_time",),
                "fixed_to_close": ("start_time",),
                "start_to_close": ("start_time",),
                "event": ("event", "active_ad"),
            }
            missing = [key for key in required_by_policy.get(policy, ()) if not parameters.get(key)]
            if missing:
                raise serializers.ValidationError({
                    "parameters": f"Для правила {policy} обязательны: {', '.join(missing)}."
                })
            for key in ("timedelta", "start_time", "end_time"):
                if key in parameters:
                    _require_clock_value(parameters, key)
            if policy == "start_to_close":
                _validate_start_time_in_workday(parameters["start_time"], nomenclature)
            if policy == "fixed_time" and parameters["start_time"] >= parameters["end_time"]:
                raise serializers.ValidationError({"parameters": "start_time должен быть раньше end_time."})
            attrs["parameters"] = parameters
            missing_dates = {
                field: "Для рекламного заказа укажите начало и окончание периода."
                for field, value in (("starts_at", starts_at), ("ends_at", ends_at))
                if value is None
            }
            if missing_dates:
                raise serializers.ValidationError(missing_dates)
        return attrs


class UnifiedOrderResendSerializer(serializers.Serializer):
    """Explicit batch payload for re-sending existing Player orders."""

    order_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100,
        help_text="От одного до 100 UUID заказов со статусом «ожидает» или «в эфире».",
    )

    def validate_order_ids(self, order_ids):
        if len(set(order_ids)) != len(order_ids):
            raise serializers.ValidationError("Один и тот же заказ указан несколько раз.")
        return order_ids
