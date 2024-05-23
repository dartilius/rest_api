from uuid import uuid4

from django.contrib.postgres.validators import KeysValidator
from django.core.validators import MaxValueValidator
from django.db import models
from django.contrib.postgres.fields import HStoreField

from users.models import CustomUser

TIMEZONES = {
    'Etc/GMT+11': 'UTC -11',
    'Etc/GMT+10': 'UTC -10',
    'Etc/GMT+9': 'UTC -9',
    'Etc/GMT+8': 'UTC -8',
    'Etc/GMT+7': 'UTC -7',
    'Etc/GMT+6': 'UTC -6',
    'Etc/GMT+5': 'UTC -5',
    'Etc/GMT+4': 'UTC -4',
    'Etc/GMT+3': 'UTC -3',
    'Etc/GMT+2': 'UTC -2',
    'Etc/GMT+1': 'UTC -1',
    'Etc/GMT+0': 'UTC',
    'Etc/GMT-1': 'UTC +1',
    'Etc/GMT-2': 'UTC +2',
    'Etc/GMT-3': 'UTC +3',
    'Etc/GMT-4': 'UTC +4',
    'Etc/GMT-5': 'UTC +5',
    'Etc/GMT-6': 'UTC +6',
    'Etc/GMT-7': 'UTC +7',
    'Etc/GMT-8': 'UTC +8',
    'Etc/GMT-9': 'UTC +9',
    'Etc/GMT-10': 'UTC +10',
    'Etc/GMT-11': 'UTC +11',
    'Etc/GMT-12': 'UTC +12'
}

DAYS = {
    1: 'Понедельник',
    2: 'Вторник',
    3: 'Среда',
    4: 'Четверг',
    5: 'Пятница',
    6: 'Суббота',
    7: 'Воскресенье'
}

STATUSES = {
    0: 'Online',
    1: 'Offline 5+ minutes',
    2: 'Offline 1+ hour'
}


class Nomenclature(models.Model):
    """Рабочая станция."""

    keys_validator = KeysValidator(
        keys=('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'),
        strict=True
    )

    id = models.UUIDField(
        default=uuid4,
        primary_key=True,
        unique=True,
        editable=False,
        verbose_name='Уникальный идентификатор'
    )
    owner = models.ForeignKey(
        CustomUser,
        related_name='nomenclatures',
        verbose_name='Создатель',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Наименование',
        unique=True
    )
    timezone = models.CharField(
        choices=TIMEZONES,
        max_length=31,
        verbose_name='Часовой пояс',
        default='Etc/GMT-7'
    )
    is_active = models.BooleanField(
        verbose_name='Актуальность номенклтауры',
        default=True
    )
    status = models.PositiveSmallIntegerField(
        choices=STATUSES,
        verbose_name='Статус',
        default=2
    )
    version = models.CharField(
        max_length=127,
        verbose_name='Версия ПО'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Описание'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    settings = HStoreField(
        verbose_name='Настройки вещания',
        validators=(keys_validator,)
    )
    hw_info = HStoreField(
        verbose_name='Информация о железе',
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'nomenclature'
        ordering = ('-created',)
        verbose_name = 'Номенклатуру'
        verbose_name_plural = 'Номенклатуры'

    def __str__(self):
        return self.name


class NomenclatureGroup(models.Model):
    """Группа номенклатур."""

    clients = models.ManyToManyField(
        Nomenclature,
        verbose_name='Рабочие станции',
        related_name='nomenclature_groups'
    )
    owner = models.ForeignKey(
        CustomUser,
        related_name='nomenclature_groups',
        verbose_name='Создатель',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Название',
        unique=True
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Описание'
    )
    created = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )

    class Meta:
        db_table = 'group'
        ordering = ('-created',)
        verbose_name = 'Группу'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.name


class NomenclatureAvailability(models.Model):
    last_answer_date = models.DateTimeField(
        auto_now=True,
        verbose_name='Время последнего ответа',
    )
    client = models.OneToOneField(
        Nomenclature,
        verbose_name='Рабочая станция',
        related_name='availability',
        on_delete=models.CASCADE
    )
    status = models.PositiveSmallIntegerField(
        choices=STATUSES,
        verbose_name='Статус',
        default=2
    )

    class Meta:
        db_table = 'availability'
        ordering = ('-last_answer_date',)
        verbose_name = 'Время последнего ответа'
        verbose_name_plural = 'Время последнего ответа'

    def __str__(self):
        return f'{self.last_answer_date}'


class StatusHistory(models.Model):
    """История изменения доступности."""

    client = models.ForeignKey(
        Nomenclature,
        verbose_name='Рабочая станция',
        related_name='history',
        on_delete=models.CASCADE
    )
    change_time = models.DateTimeField(
        verbose_name='Время изменения статуса',
        auto_now_add=True
    )
    status = models.PositiveSmallIntegerField(
        choices=STATUSES,
        verbose_name='Статус'
    )

    class Meta:
        db_table = 'status_history'
        ordering = ('-change_time',)
        verbose_name = 'Историю доступности'
        verbose_name_plural = 'История доступности'

    def __str__(self):
        return (
            f'{self.change_time.strftime("%Y-%m-%d %H:%M:%S")}: ' 
            f'статус {self.client.name} '
            f'изменился на {STATUSES[self.status][1]}'
        )
