"""Регистрация ключей и команд Player v2 в Django admin."""

from django import forms
from django.contrib import admin, messages

from nomenclatures.models import Nomenclature, StationCommandV2, StationCredential
from nomenclatures.settings_patch import SettingsPatchError, apply_settings_operations
from nomenclatures.station_credentials import (
    generate_station_token,
    hash_station_token,
    issue_station_token,
)


DAY_CHOICES = (
    ("mon", "Понедельник"),
    ("tue", "Вторник"),
    ("wed", "Среда"),
    ("thu", "Четверг"),
    ("fri", "Пятница"),
    ("sat", "Суббота"),
    ("sun", "Воскресенье"),
)
SETTING_GROUP_CHOICES = (
    ("volume", "Громкость канала"),
    ("background", "Параметр фона"),
    ("worktime", "Рабочее время"),
    ("audio_device", "Аудиовыход Player"),
    ("display", "Экран вывода Player"),
    ("visual_output", "Поворот визуального вывода"),
)
BACKGROUND_SETTING_CHOICES = (
    ("video_enabled", "Показывать фоновое видео"),
    ("video_muted", "Выключить звук фонового видео"),
    ("img_enabled", "Показывать фоновые картинки"),
    ("img_duration", "Время показа картинки"),
    ("music_random", "Случайный порядок фоновой музыки"),
    ("video_random", "Случайный порядок фонового видео"),
    ("img_random", "Случайный порядок фоновых картинок"),
)
BACKGROUND_BOOLEAN_VALUES = (("true", "Включено"), ("false", "Выключено"))


def _latest_saved_revision(nomenclature) -> int:
    """Возвращает последнюю revision, подтверждённую Player, а не admin-формой."""
    if nomenclature.applied_settings_revision is not None:
        return nomenclature.applied_settings_revision

    commands = StationCommandV2.objects.filter(
        nomenclature=nomenclature,
        status=StationCommandV2.Status.APPLIED,
    ).order_by("-updated_at")
    for command in commands:
        revision = (command.result or {}).get("saved_revision")
        if isinstance(revision, int) and not isinstance(revision, bool) and revision >= 0:
            return revision
    return 0


def _station_audio_devices(nomenclature):
    """Return only valid device records published by this Player."""
    capabilities = nomenclature.station_capabilities or {}
    audio = capabilities.get("audio") if isinstance(capabilities, dict) else None
    devices = audio.get("devices") if isinstance(audio, dict) else None
    if not isinstance(devices, list):
        return []
    return [
        device for device in devices
        if isinstance(device, dict) and isinstance(device.get("id"), str) and device["id"]
    ]


def _audio_device_choices():
    """Offer published choices; clean() still authorizes against selected station."""
    choices = [("", "Сначала выберите точку вещания")]
    for nomenclature in Nomenclature.objects.exclude(station_capabilities__isnull=True).only(
        "name", "station_capabilities"
    ):
        for device in _station_audio_devices(nomenclature):
            choices.append((device["id"], f"{device.get('name', device['id'])} — {nomenclature.name}"))
    return choices


def _station_displays(nomenclature):
    capabilities = nomenclature.station_capabilities or {}
    displays = capabilities.get("displays") if isinstance(capabilities, dict) else None
    if not isinstance(displays, list):
        return []
    return [
        display for display in displays
        if isinstance(display, dict) and isinstance(display.get("id"), str) and display["id"]
    ]


def _display_choices():
    choices = [("", "Сначала выберите точку вещания")]
    for nomenclature in Nomenclature.objects.exclude(station_capabilities__isnull=True).only(
        "name", "station_capabilities"
    ):
        for display in _station_displays(nomenclature):
            choices.append((display["id"], f"{display.get('name', display['id'])} — {nomenclature.name}"))
    return choices


class StationVolumeCommandForm(forms.ModelForm):
    """Понятная оператору форма для одного безопасного изменения Player."""

    setting_group = forms.ChoiceField(label="Что изменить", choices=SETTING_GROUP_CHOICES)
    day = forms.ChoiceField(label="День", choices=DAY_CHOICES)
    all_days = forms.BooleanField(label="Применить ко всем дням", required=False)
    source = forms.ChoiceField(
        label="Контент",
        choices=(("background", "Фон"), ("advertisement", "Реклама")),
        required=False,
    )
    channel = forms.ChoiceField(
        label="Канал", choices=(("left", "Левый"), ("right", "Правый")), required=False
    )
    volume = forms.IntegerField(label="Громкость, %", min_value=0, max_value=100, required=False)
    background_setting = forms.ChoiceField(
        label="Параметр фона",
        choices=BACKGROUND_SETTING_CHOICES,
        required=False,
        help_text="Для времени показа используйте поле ниже; для остальных — «Значение». ",
    )
    background_enabled = forms.ChoiceField(
        label="Значение",
        choices=BACKGROUND_BOOLEAN_VALUES,
        required=False,
    )
    image_duration = forms.IntegerField(
        label="Время показа картинки, сек.",
        min_value=1,
        max_value=60,
        required=False,
    )
    audio_device_id = forms.ChoiceField(
        label="Аудиовыход",
        choices=(),
        required=False,
    )
    display_id = forms.ChoiceField(label="Экран вывода", choices=(), required=False)
    visual_output_rotation = forms.ChoiceField(
        label="Поворот контента",
        choices=(("0", "Без поворота"), ("90", "90°"), ("180", "180°"), ("270", "270°")),
        required=False,
    )
    full_day = forms.BooleanField(label="Круглосуточно", required=False)
    worktime_start = forms.TimeField(
        label="Начало вещания",
        input_formats=("%H:%M", "%H:%M:%S"),
        required=False,
    )
    worktime_end = forms.TimeField(
        label="Конец вещания",
        input_formats=("%H:%M", "%H:%M:%S"),
        required=False,
    )

    class Meta:
        model = StationCommandV2
        fields = ("nomenclature",)
        labels = {"nomenclature": "Точка вещания"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["audio_device_id"].choices = _audio_device_choices()
        self.fields["display_id"].choices = _display_choices()

    def clean(self):
        cleaned_data = super().clean()
        setting_group = cleaned_data.get("setting_group")
        nomenclature = cleaned_data.get("nomenclature")
        if nomenclature is None:
            return cleaned_data
        if setting_group == "volume":
            for field in ("source", "channel", "volume"):
                if cleaned_data.get(field) is None:
                    self.add_error(field, "Заполните поле для изменения громкости.")
        elif setting_group == "background":
            background_setting = cleaned_data.get("background_setting")
            if background_setting is None:
                self.add_error("background_setting", "Выберите параметр фона.")
            elif background_setting == "img_duration":
                if cleaned_data.get("image_duration") is None:
                    self.add_error("image_duration", "Укажите время показа картинки.")
            elif cleaned_data.get("background_enabled") is None:
                self.add_error("background_enabled", "Выберите, включить или выключить параметр.")
        elif setting_group == "worktime" and not cleaned_data.get("full_day"):
            start = cleaned_data.get("worktime_start")
            end = cleaned_data.get("worktime_end")
            if start is None:
                self.add_error("worktime_start", "Укажите начало вещания.")
            if end is None:
                self.add_error("worktime_end", "Укажите конец вещания.")
            if start is not None and end is not None and start >= end:
                self.add_error("worktime_end", "Конец должен быть позже начала в пределах одного дня.")
        elif setting_group == "audio_device":
            device_id = cleaned_data.get("audio_device_id")
            available_ids = {device["id"] for device in _station_audio_devices(nomenclature)}
            if not device_id:
                self.add_error("audio_device_id", "Выберите аудиовыход Player.")
            elif device_id not in available_ids:
                self.add_error("audio_device_id", "Этот аудиовыход не принадлежит выбранной точке.")
        elif setting_group == "display":
            display_id = cleaned_data.get("display_id")
            available_ids = {display["id"] for display in _station_displays(nomenclature)}
            if not display_id:
                self.add_error("display_id", "Выберите экран вывода Player.")
            elif display_id not in available_ids:
                self.add_error("display_id", "Этот экран не принадлежит выбранной точке.")
        elif setting_group == "visual_output" and not cleaned_data.get("visual_output_rotation"):
            self.add_error("visual_output_rotation", "Выберите поворот визуального контента.")
        pending_kind = (
            "select_audio_device" if setting_group == "audio_device"
            else "select_display" if setting_group == "display"
            else "set_visual_output" if setting_group == "visual_output"
            else "apply_settings_patch"
        )
        if StationCommandV2.objects.filter(
            nomenclature=nomenclature,
            status=StationCommandV2.Status.PENDING,
            kind=pending_kind,
        ).exists():
            raise forms.ValidationError(
                "У этой точки уже есть ожидающее изменение настроек. "
                "Дождитесь результата Player перед созданием следующего."
            )
        return cleaned_data

    def save(self, commit=True):
        command = super().save(commit=False)
        nomenclature = self.cleaned_data["nomenclature"]
        if self.cleaned_data["setting_group"] == "audio_device":
            command.kind = "select_audio_device"
            command.body = {"device_id": self.cleaned_data["audio_device_id"]}
            if commit:
                command.save()
            return command
        if self.cleaned_data["setting_group"] == "display":
            command.kind = "select_display"
            command.body = {"display_id": self.cleaned_data["display_id"]}
            if commit:
                command.save()
            return command
        if self.cleaned_data["setting_group"] == "visual_output":
            command.kind = "set_visual_output"
            command.body = {"rotation": int(self.cleaned_data["visual_output_rotation"])}
            if commit:
                command.save()
            return command
        command.kind = "apply_settings_patch"
        target_days = (
            tuple(day_key for day_key, _ in DAY_CHOICES)
            if self.cleaned_data["all_days"]
            else (self.cleaned_data["day"],)
        )
        if self.cleaned_data["setting_group"] == "background":
            background_setting = self.cleaned_data["background_setting"]
            value = (
                self.cleaned_data["image_duration"]
                if background_setting == "img_duration"
                else self.cleaned_data["background_enabled"] == "true"
            )
            operations = [
                {
                    "op": "set",
                    "path": f"/days/{day}/background/{background_setting}",
                    "value": value,
                }
                for day in target_days
            ]
        elif self.cleaned_data["setting_group"] == "worktime":
            worktime = (
                "00:00:00-23:59:59"
                if self.cleaned_data["full_day"]
                else (
                    f"{self.cleaned_data['worktime_start'].strftime('%H:%M:%S')}-"
                    f"{self.cleaned_data['worktime_end'].strftime('%H:%M:%S')}"
                )
            )
            operations = [
                {"op": "set", "path": f"/days/{day}/worktime", "value": worktime}
                for day in target_days
            ]
        else:
            operations = [
                {
                    "op": "set",
                    "path": (
                        f"/days/{day}/default_volume/"
                        f"{self.cleaned_data['source']}/{self.cleaned_data['channel']}"
                    ),
                    "value": self.cleaned_data["volume"],
                }
                for day in target_days
            ]
        command.body = {
            "base_revision": _latest_saved_revision(nomenclature),
            "operations": operations,
        }
        try:
            apply_settings_operations(nomenclature.settings, operations)
        except SettingsPatchError as exc:
            raise forms.ValidationError(
                "Невозможно подготовить изменение: сохранённые настройки точки некорректны."
            ) from exc
        if commit:
            command.save()
        return command


@admin.register(StationCredential)
class StationCredentialAdmin(admin.ModelAdmin):
    list_display = ("nomenclature", "is_active", "rotated_at")
    list_filter = ("is_active",)
    search_fields = ("nomenclature__name", "nomenclature__code1c")
    autocomplete_fields = ("nomenclature",)
    readonly_fields = ("token_hash", "created_at", "rotated_at")
    fields = ("nomenclature", "is_active", "token_hash", "created_at", "rotated_at")
    actions = ("rotate_tokens",)

    @admin.action(description="Rotate station tokens")
    def rotate_tokens(self, request, queryset):
        tokens = [issue_station_token(credential) for credential in queryset]
        if not tokens:
            return
        if len(tokens) == 1:
            self.message_user(
                request,
                f"New station token (copy now; it will not be shown again): {tokens[0]}",
                level=messages.WARNING,
            )
            return
        self.message_user(
            request,
            f"Rotated {len(tokens)} station tokens. Rotate one station at a time to copy its token.",
            level=messages.WARNING,
        )

    def save_model(self, request, obj, form, change):
        if change:
            super().save_model(request, obj, form, change)
            return

        token = generate_station_token()
        obj.token_hash = hash_station_token(token)
        super().save_model(request, obj, form, change)
        self.message_user(
            request,
            f"Station token (copy now; it will not be shown again): {token}",
            level=messages.WARNING,
        )


@admin.register(StationCommandV2)
class StationCommandV2Admin(admin.ModelAdmin):
    """Ставит в очередь одну безопасную и понятную оператору команду."""

    form = StationVolumeCommandForm
    list_display = ("nomenclature", "kind", "delivery_state", "created_at", "updated_at")
    list_filter = ("status", "kind")
    search_fields = ("nomenclature__name", "nomenclature__code1c", "command_id")
    autocomplete_fields = ("nomenclature",)
    readonly_fields = (
        "command_id",
        "kind",
        "body",
        "result",
        "delivered_at",
        "created_at",
        "updated_at",
    )

    @admin.display(description="Состояние доставки", ordering="delivered_at")
    def delivery_state(self, obj):
        if obj.status == StationCommandV2.Status.APPLIED:
            return "Применена"
        if obj.status == StationCommandV2.Status.FAILED:
            return "Ошибка применения"
        if obj.delivered_at is not None:
            return "Доставлена, ждёт подтверждения"
        return "Ожидает отправки"

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return (
                (
                    "Область изменения",
                    {"fields": ("nomenclature", "setting_group", "day", "all_days")},
                ),
                (
                    "Громкость канала",
                    {"fields": ("source", "channel", "volume")},
                ),
                (
                    "Фоновый контент",
                    {
                        "fields": (
                            "background_setting",
                            "background_enabled",
                            "image_duration",
                        )
                    },
                ),
                (
                    "Рабочее время",
                    {"fields": ("full_day", "worktime_start", "worktime_end")},
                ),
                ("Аудиовыход Player", {"fields": ("audio_device_id",)}),
                ("Экран вывода Player", {"fields": ("display_id",)}),
                (
                    "Поворот визуального вывода",
                    {"fields": ("visual_output_rotation",)},
                ),
            )
        return (("Команда", {"fields": ("nomenclature",) + self.readonly_fields}),)

    def has_change_permission(self, request, obj=None):
        return False
