from django.contrib.postgres.validators import KeysValidator
from django.db import models

from api import APIBaseObjectModel, Article

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


class Nomenclature(APIBaseObjectModel):
    """Рабочая станция."""

    keys_validator = KeysValidator(
        keys=('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'),
        strict=True
    )

    article = Article()
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Описание'
    )
    timezone = models.CharField(
        choices=TIMEZONES,
        max_length=31,
        verbose_name='Часовой пояс',
        default='Etc/GMT-7'
    )
    version = models.CharField(
        max_length=127,
        verbose_name='Версия ПО'
    )
    settings = models.JSONField(
        verbose_name='Настройки вещания',
        validators=(keys_validator,)
    )
    hw_info = models.JSONField(
        verbose_name='Информация о железе',
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'nomenclature'
        ordering = ('-created',)
        verbose_name = 'Номенклатура'
        verbose_name_plural = 'Номенклатуры'
        constraints = [
            models.UniqueConstraint(
                fields=['name'],
                name='unique_nomenclature_name',
                violation_error_message='Номенклатура с таким названием '
                                        'уже существует'
            )
        ]


class NomenclatureAvailability(models.Model):
    """Текущая доступность."""
    last_answer_date = models.DateTimeField(
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
        verbose_name = 'История доступности'
        verbose_name_plural = 'История доступности'

    def __str__(self):
        return (
            f'{self.change_time.strftime("%Y-%m-%d %H:%M:%S")}: ' 
            f'статус {self.client.name} '
            f'изменился на {STATUSES[self.status][1]}'
        )
