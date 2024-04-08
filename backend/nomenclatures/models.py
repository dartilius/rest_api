from uuid import uuid4

from django.core.validators import MaxValueValidator
from django.db import models
from django.contrib.postgres.fields import ArrayField

from users.models import User

TIMEZONES = [
    ("Etc/GMT+11", "UTC-11"),
    ("Etc/GMT+10", "UTC-10"),
    ("Etc/GMT+9", "UTC-9"),
    ("Etc/GMT+8", "UTC-8"),
    ("Etc/GMT+7", "UTC-7"),
    ("Etc/GMT+6", "UTC-6"),
    ("Etc/GMT+5", "UTC-5"),
    ("Etc/GMT+4", "UTC-4"),
    ("Etc/GMT+3", "UTC-3"),
    ("Etc/GMT+2", "UTC-2"),
    ("Etc/GMT+1", "UTC-1"),
    ("Etc/GMT+0", "UTC"),
    ("Etc/GMT-1", "UTC+1"),
    ("Etc/GMT-2", "UTC+2"),
    ("Etc/GMT-3", "UTC+3"),
    ("Etc/GMT-4", "UTC+4"),
    ("Etc/GMT-5", "UTC+5"),
    ("Etc/GMT-6", "UTC+6"),
    ("Etc/GMT-7", "UTC+7"),
    ("Etc/GMT-8", "UTC+8"),
    ("Etc/GMT-9", "UTC+9"),
    ("Etc/GMT-10", "UTC+10"),
    ("Etc/GMT-11", "UTC+11"),
    ("Etc/GMT-12", "UTC+12")
]

DAYS = [
    (1, "Понедельник"),
    (2, "Вторник"),
    (3, "Среда"),
    (4, "Четверг"),
    (5, "Пятница"),
    (6, "Суббота"),
    (7, "Воскресенье")
]

STATUSES = [
    (0, "Online"),
    (1, "Offline 5+ minutes"),
    (2, "Offline 1+ hour")
]


class Settings(models.Model):
    """Настройки микрокомпьютера."""

    days = ArrayField(
        models.PositiveSmallIntegerField(
            # choices=DAYS
        ),
        verbose_name="Дни недели",
        size=7
    )
    start_time = models.TimeField(
        verbose_name="Время начала работы"
    )
    end_time = models.TimeField(
        verbose_name="Время оончания работы"
    )
    """
        Методика хранения массива дней мне кажется неоптимальной,
        возможны баги, к примеру будут указаны не все дни недели,
        что поведет за собой отключение вещания в не указанные дни.
        Хранить режим работы лучше в range field и использовать
        целочисленный интервал с максимальным значением 86399 и
        минимальным значением 0 (00:00:00 - 23:59:59)
        
        Для исключения бага можно вынести дефолтный режим работы
        и громкость в модель номенклатуры, а настройки считать 
        приоритетнее дефолтных настроек, в таком случае эта модель
        будет использоваться для нестандартных случаев.
    """
    volumes = models.JSONField(
        verbose_name="Настройки громкости"
    )
    default_volume = ArrayField(
        models.PositiveSmallIntegerField(
            validators=[
                MaxValueValidator(100)
            ]
        ),
        size=4,
        verbose_name="Громкость по умолчанию"
    )

    class Meta:
        verbose_name = 'Настройка номенклатуры'
        verbose_name_plural = 'Настройки номенклатуры'

    def __str__(self):
        return f"{self.days}"


class Nomenclature(models.Model):
    """Рабочая станция."""

    id = models.UUIDField(
        default=uuid4,
        primary_key=True,
        unique=True,
        editable=False,
        verbose_name="Уникальный идентификатор"
    )
    owner = models.ForeignKey(
        User,
        related_name="nomenclature",
        verbose_name="Создатель",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Наименование"
    )
    timezone = models.CharField(
        choices=TIMEZONES,
        max_length=31,
        verbose_name="Часовой пояс",
        default="Etc/GMT-7"
    )
    is_active = models.BooleanField(
        verbose_name="Актуальность номенклтауры",
        default=True
    )
    status = models.PositiveSmallIntegerField(
        choices=STATUSES,
        verbose_name="Статус",
        default=2
    )
    version = models.CharField(
        max_length=127,
        verbose_name="Версия ПО"
    )
    description = models.TextField(
        verbose_name="Описание"
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    settings = models.ManyToManyField(
        Settings,
        related_name="nomenclature_settings",
        verbose_name="Настройки вещания"
    )

    class Meta:
        verbose_name = 'Номенклатура'
        verbose_name_plural = 'Номенклатуры'

    def __str__(self):
        return self.name


class HardWareInfo(models.Model):
    """Информация о железе."""

    client = models.OneToOneField(
        Nomenclature,
        primary_key=True,
        related_name="nomenclature_hwinfo",
        verbose_name="Номенклатура",
        on_delete=models.CASCADE
    )
    city = models.CharField(
        max_length=255,
        verbose_name="Город"
    )
    model = models.CharField(
        max_length=255,
        verbose_name="Модель"
    )
    internet_service_provider = models.CharField(
        max_length=255,
        verbose_name="Интернет провайдер"
    )
    external_ip = models.GenericIPAddressField(
        verbose_name="IP адресс"
    )
    network_config = models.JSONField(
        verbose_name="Настройки сети"
    )
    audio_device = models.JSONField(
        verbose_name="Звуковые карты"
    )

    class Meta:
        verbose_name = 'Информация о железе'
        verbose_name_plural = 'Информация о железе'

    def __str__(self):
        return self.client.name


class NomenclatureGroup(models.Model):
    """Группа номенклатур."""

    clients = models.ManyToManyField(
        Nomenclature,
        verbose_name="Рабочие станции",
        related_name="nomenclature_group"
    )
    owner = models.ForeignKey(
        User,
        verbose_name="Создатель",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Название"
    )
    description = models.TextField(
        verbose_name="Описание"
    )
    created = models.DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.name


class StatusHistory(models.Model):
    """История изменения доступности."""

    client = models.ForeignKey(
        Nomenclature,
        verbose_name="Рабочая станция",
        on_delete=models.CASCADE
    )
    change_time = models.DateTimeField(
        verbose_name="Время изменения статуса",
        auto_now_add=True
    )
    status = models.PositiveSmallIntegerField(
        choices=STATUSES,
        verbose_name="Статус"
    )

    class Meta:
        verbose_name = 'История доступности'
        verbose_name_plural = 'История доступности'

    def __str__(self):
        return (
            f"{self.change_time}: " 
            f"статус {self.client.id} изменился на {self.status}"
        )
