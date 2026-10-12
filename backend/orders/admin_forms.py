"""Typed Django-admin form for unified Player orders.

The transport keeps ``Order.parameters`` as JSON for the API and Player, but
managers configure its supported values through ordinary form controls.
"""

from __future__ import annotations

from datetime import time, timedelta
import logging

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as RestValidationError

from nomenclatures.models import Nomenclature
from orders.models import Order
from orders.services.unified_order_delivery import validate_order_delivery
from orders.unified_serializers import UnifiedOrderSerializer


logger = logging.getLogger(__name__)


class ClockInput(forms.TimeInput):
    input_type = "time"

_SCHEDULE_KEYS = {
    "times_in_hour", "timedelta", "start_time", "end_time", "schedule_mode",
}
_POLICY_FIELDS = {
    "open_offset": ("timedelta",),
    "close_offset": ("timedelta",),
    "fixed_time": ("start_time", "end_time"),
    "open_to_fixed": ("end_time",),
    "fixed_to_close": ("start_time",),
    "start_to_close": ("start_time",),
}


class UnifiedOrderAdminForm(forms.ModelForm):
    """Admin-only projection of managed JSON parameters into typed fields."""

    target_nomenclatures = forms.ModelMultipleChoiceField(
        queryset=Nomenclature.objects.none(),
        required=False,
        label="Точки вещания",
        help_text="Для каждой выбранной точки будет создан отдельный заказ и команда Player.",
        widget=FilteredSelectMultiple("Точки вещания", is_stacked=False),
    )
    times_in_hour = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=60,
        initial=1,
        label="Выходов в час",
        help_text="От 1 до 60 выходов заказа за час. Например, 4 — один выход примерно каждые 15 минут. Ролики выбираются по очереди.",
        widget=forms.NumberInput(attrs={"class": "js-ad-schedule"}),
    )
    start_time = forms.TimeField(
        required=False,
        input_formats=("%H:%M:%S", "%H:%M"),
        label="Начинать показы с",
        help_text="Для фиксированного времени, «с указанного времени до закрытия» и других режимов, где нужно начало.",
        widget=ClockInput(format="%H:%M:%S", attrs={"step": "1", "class": "js-ad-schedule"}),
    )
    end_time = forms.TimeField(
        required=False,
        input_formats=("%H:%M:%S", "%H:%M"),
        label="Заканчивать показы в",
        help_text="Для фиксированного времени и режима «от открытия до указанного времени».",
        widget=ClockInput(format="%H:%M:%S", attrs={"step": "1", "class": "js-ad-schedule"}),
    )
    offset_minutes = forms.IntegerField(required=False, min_value=0, max_value=5999, initial=0,
        label="Отступ, минут", help_text="Например, 30 — начать через полчаса после открытия или закончить за полчаса до закрытия.")
    offset_seconds = forms.IntegerField(required=False, min_value=0, max_value=59, initial=0,
        label="Дополнительно секунд", help_text="Обычно 0. Например, 5 минут и 30 секунд задаются двумя числами: 5 и 30.")
    order_weight = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
        initial=50,
        label="Приоритет заказа",
        help_text="Для рекламы, фоновых видео и картинок: большее число ставит заказ раньше в очереди, а не чаще. Обычно оставляют 50.",
        widget=forms.NumberInput(attrs={"class": "js-order-priority"}),
    )
    image_duration_seconds = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=86400,
        label="Показ картинки, секунд",
        help_text="Если в плейлисте есть картинки, задайте время их показа. Пусто — используется настройка плеера. Видео всегда играется полностью.",
        widget=forms.NumberInput(attrs={"class": "js-order-image-duration"}),
    )
    advertising_audio = forms.ChoiceField(
        choices=(("sound", "Со звуком"), ("muted", "Без звука")),
        initial="sound",
        required=False,
        label="Звук рекламы",
        help_text="У непрерывной рекламы без звука фоновая музыка продолжает играть.",
        widget=forms.Select(attrs={"class": "js-ad-option"}),
    )

    class Meta:
        model = Order
        exclude = ("parameters",)
        labels = {
            "placement": "Что отправляем", "playback_policy": "Как показывать рекламу",
            "playlist": "Плейлист с контентом", "starts_at": "Начало периода", "ends_at": "Конец периода",
            "is_permanent": "Фон без даты окончания",
            "suppress_background_audio": "Останавливать фоновую музыку на время рекламы",
            "suppress_background_visual": "Приостанавливать фоновые видео и картинки на время рекламы",
        }
        help_texts = {
            "name": "Понятное название, чтобы потом найти заказ. Например: «Осенняя акция».",
            "playlist": "Начните вводить название и выберите плейлист из списка. Его ролики будут воспроизводиться по очереди.",
            "starts_at": "Дата начала действия заказа. Для рекламы также нужно время; для фона пустое поле означает запуск после загрузки.",
            "ends_at": "После этого времени заказ больше не воспроизводится.",
            "is_permanent": "Только для фона. Он не заканчивается по дате и используется, когда нет активного срочного фона этого типа.",
            "suppress_background_audio": "Снимите галочку, если музыка должна продолжать играть под рекламой без звука.",
            "suppress_background_visual": "Обычно эту галочку оставляют: на экране будет реклама вместо фонового видео или картинки.",
        }
        widgets = {
            "placement": forms.Select(attrs={"class": "js-order-placement"}),
            "playback_policy": forms.Select(attrs={"class": "js-order-policy"}),
            "suppress_background_audio": forms.CheckboxInput(attrs={"class": "js-ad-option"}),
            "suppress_background_visual": forms.CheckboxInput(attrs={"class": "js-ad-option"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "playback_policy" not in self.fields:
            return  # The admin can request an entirely read-only form.
        parameters = self.instance.parameters if isinstance(self.instance.parameters, dict) else {}
        adding = self.instance._state.adding

        if adding:
            if "nomenclature" in self.fields:
                self.fields["nomenclature"].required = False
                self.fields["nomenclature"].widget = forms.HiddenInput()
            self.fields["target_nomenclatures"].queryset = Nomenclature.active.order_by("name")
            self.fields["suppress_background_audio"].initial = True
            self.fields["suppress_background_visual"].initial = True
            self.initial["suppress_background_audio"] = True
            self.initial["suppress_background_visual"] = True
            self.initial["placement"] = self.initial.get("placement") or "advertising"
        else:
            self.fields["target_nomenclatures"].widget = forms.HiddenInput()
            self.fields["target_nomenclatures"].disabled = True

        self.fields["times_in_hour"].initial = parameters.get("times_in_hour", 1)
        self.fields["order_weight"].initial = parameters.get("weight", 50)
        self.fields["image_duration_seconds"].initial = parameters.get("image_duration_seconds")
        self.fields["advertising_audio"].initial = "muted" if parameters.get("audio_muted") else "sound"
        offset = _parse_offset(parameters.get("timedelta"))
        seconds = int(offset.total_seconds()) if offset is not None else 0
        self.fields["offset_minutes"].initial, self.fields["offset_seconds"].initial = divmod(seconds, 60)
        for field in ("start_time", "end_time"):
            raw_value = parameters.get(field)
            if raw_value:
                try:
                    self.fields[field].initial = time.fromisoformat(raw_value)
                except (TypeError, ValueError):
                    logger.warning("Order %s has invalid %s: %r", self.instance.pk, field, raw_value)

        choices = list(self.fields["playback_policy"].choices)
        self.fields["playback_policy"].required = False
        if adding or self.instance.playback_policy != "event":
            choices = [choice for choice in choices if choice[0] != "event"]
        if adding or self.instance.playback_policy != "hourly_slots":
            choices = [choice for choice in choices if choice[0] != "hourly_slots"]
        if not adding and self.instance.playback_policy == "event":
            self.fields["playback_policy"].disabled = True
            self.fields["playback_policy"].help_text = (
                "Реклама по событию пока не настраивается в админке. Существующие параметры сохранены без изменений."
            )
            self.fields["playback_policy"].widget.attrs["class"] += " js-unsupported-event"
        self.fields["playback_policy"].choices = choices
        selected_placement = self.data.get(self.add_prefix("placement"), self.instance.placement)
        permanent = self.fields["is_permanent"].widget.value_from_datadict(self.data, self.files, self.add_prefix("is_permanent"))
        if self.is_bound and selected_placement == "background" and permanent:
            self.fields["ends_at"].disabled = True
            self.initial["ends_at"] = None

    def clean(self):
        cleaned_data = super().clean()
        placement = cleaned_data.get("placement", self.instance.placement)
        policy = cleaned_data.get("playback_policy") or self.instance.playback_policy
        cleaned_data["placement"] = placement
        cleaned_data["playback_policy"] = policy
        stored = self.instance.parameters or {}
        if not isinstance(stored, dict):
            self.instance.parameters = {}
            self.add_error(None, "Сохранённые настройки заказа повреждены. Обратитесь к администратору.")
            return cleaned_data
        parameters = dict(stored)
        targets = list(cleaned_data.get("target_nomenclatures") or ())

        if self.instance._state.adding:
            if not targets:
                self.add_error("target_nomenclatures", "Выберите хотя бы одну точку вещания.")
            else:
                cleaned_data["nomenclature"] = targets[0]
                self.instance.nomenclature = targets[0]

        if placement == "background":
            cleaned_data["playback_policy"] = "workday"
            policy = "workday"
            cleaned_data["ends_at"] = None if cleaned_data.get("is_permanent") else cleaned_data.get("ends_at")
            if not cleaned_data.get("is_permanent") and cleaned_data.get("ends_at") is None:
                self.add_error("ends_at", "Укажите конец периода или включите «Фон без даты окончания».")
            parameters.pop("audio_muted", None)
            parameters.pop("event", None)
            parameters.pop("active_ad", None)
            for key in _SCHEDULE_KEYS:
                parameters.pop(key, None)
        elif placement == "advertising" and policy != "event":
            for key in _SCHEDULE_KEYS:
                parameters.pop(key, None)
            self._collect_advertising_parameters(cleaned_data, parameters, policy, targets)
        elif placement == "advertising" and policy == "event":
            cleaned_data["suppress_background_audio"] = self.instance.suppress_background_audio
            cleaned_data["suppress_background_visual"] = self.instance.suppress_background_visual

        self._collect_visual_parameters(cleaned_data, parameters)
        cleaned_data["parameters"] = parameters
        self.instance.parameters = parameters
        return cleaned_data

    def _collect_advertising_parameters(self, cleaned_data, parameters, policy, targets):
        if policy == "continuous":
            cleaned_data["suppress_background_audio"] = cleaned_data.get("advertising_audio") != "muted"
            cleaned_data["suppress_background_visual"] = True
            return

        times = cleaned_data.get("times_in_hour")
        if times is None:
            self.add_error("times_in_hour", "Укажите количество выходов в час.")
        else:
            parameters["times_in_hour"] = times

        required = _POLICY_FIELDS.get(policy, ())
        if "timedelta" in required:
            minutes = cleaned_data.get("offset_minutes")
            if minutes is None:
                self.add_error("offset_minutes", "Укажите отступ в минутах; 0 означает без отступа.")
            else:
                parameters["timedelta"] = _format_offset(timedelta(minutes=minutes, seconds=cleaned_data.get("offset_seconds") or 0))

        for field in ("start_time", "end_time"):
            value = cleaned_data.get(field)
            if field in required and value is None:
                self.add_error(field, "Укажите время.")
            elif field in required:
                parameters[field] = value.strftime("%H:%M:%S")

        if policy == "fixed_time":
            start, end = cleaned_data.get("start_time"), cleaned_data.get("end_time")
            if start is not None and end is not None and start >= end:
                self.add_error("end_time", "Время окончания должно быть позже времени начала.")
        if policy == "start_to_close" and cleaned_data.get("start_time") is not None:
            for nomenclature in targets or [cleaned_data.get("nomenclature") or self.instance.nomenclature]:
                if nomenclature is not None:
                    self._validate_start_time_in_workday(cleaned_data["start_time"], nomenclature)

    def _collect_visual_parameters(self, cleaned_data, parameters):
        weight = cleaned_data.get("order_weight")
        if weight is not None:
            parameters["weight"] = weight
        else:
            parameters.pop("weight", None)
        duration = cleaned_data.get("image_duration_seconds")
        if duration is None:
            parameters.pop("image_duration_seconds", None)
        else:
            parameters["image_duration_seconds"] = duration
        if cleaned_data.get("placement") == "advertising" and cleaned_data.get("playback_policy") != "event":
            parameters["audio_muted"] = cleaned_data.get("advertising_audio") == "muted"

    def _post_clean(self):
        super()._post_clean()
        if self.errors:
            return
        try:
            validated = UnifiedOrderSerializer(instance=None if self.instance._state.adding else self.instance).validate(self.cleaned_data)
        except RestValidationError as exc:
            self._add_serializer_errors(exc.detail)
            return

        self.instance.parameters = validated.get("parameters", self.instance.parameters)
        for field in ("suppress_background_audio", "suppress_background_visual"):
            if field in validated:
                self.cleaned_data[field] = validated[field]
                setattr(self.instance, field, validated[field])
        targets = (
            self.cleaned_data.get("target_nomenclatures")
            if self.instance._state.adding
            else [self.instance.nomenclature]
        )
        original = self.instance.nomenclature
        try:
            for target in targets:
                self.instance.nomenclature = target
                validate_order_delivery(self.instance)
        except ValidationError as exc:
            self.add_error(None, exc)
        finally:
            self.instance.nomenclature = original

    def _add_serializer_errors(self, details):
        for field, messages in details.items():
            target = field
            if field == "parameters":
                policy = self.cleaned_data.get("playback_policy")
                target = {
                    "open_offset": "offset_minutes",
                    "close_offset": "offset_minutes",
                    "fixed_time": "start_time",
                    "open_to_fixed": "end_time",
                    "fixed_to_close": "start_time",
                    "start_to_close": "start_time",
                }.get(policy, "times_in_hour")
            self.add_error(target if target in self.fields else None, messages)

    def _validate_start_time_in_workday(self, start_time, nomenclature) -> None:
        worktime_start = getattr(nomenclature, "worktime_start", None)
        worktime_end = getattr(nomenclature, "worktime_end", None)
        if worktime_start is None or worktime_end is None:
            return
        in_workday = (
            worktime_start <= start_time < worktime_end
            if worktime_start < worktime_end
            else start_time >= worktime_start or start_time < worktime_end
        )
        if not in_workday:
            self.add_error("start_time", "Первый выход должен быть в рабочее время точки.")


def _parse_offset(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return timedelta(minutes=value)
    if isinstance(value, str):
        try:
            hours, minutes, seconds = (int(part) for part in value.split(":"))
        except (TypeError, ValueError):
            return None
        if hours >= 0 and 0 <= minutes < 60 and 0 <= seconds < 60:
            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
    return None


def _format_offset(value: timedelta) -> str:
    seconds = int(value.total_seconds())
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
