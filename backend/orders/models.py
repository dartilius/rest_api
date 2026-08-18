# orders/models.py

from django.contrib.postgres.fields import DateTimeRangeField
from django.db import models
from django.utils import timezone

from api import APIBaseObjectModel
from nomenclatures.models import Nomenclature
from files.models import Playlist


ORDER_TYPES = {
    0: 'Фоновая музыка',
    1: 'Фоновые видео',
    2: 'Фоновые картинки',
    3: 'Бегущая строка',
}


STATUSES = {
    0: 'Ожидает эфира',
    1: 'В эфире',
    2: 'Завершён',
    3: 'Отменён',
    4: 'Ошибка',
}


BROADCAST_TYPES = {
    0: 'По времени работы точки',
    1: 'Начало работы + смещение по времени',
    2: 'Конец работы - смещение по времени',
    3: 'Конкретные часы',
    4: 'С открытия до фиксированного часа',
    5: 'С фиксированного часа до закрытия',
    6: 'Старт по событию',
}


def _format_local_datetime(value):
    """
    Приводит datetime к локальной временной зоне Django и возвращает
    строку в формате YYYY-MM-DD HH:MM:SS.

    В базе значение остаётся полноценным datetime с корректной
    временной зоной. Timezone удаляется только из строки, которая
    передаётся клиентскому ПО.
    """
    if value is None:
        return None

    if timezone.is_aware(value):
        value = timezone.localtime(value)

    return value.strftime('%Y-%m-%d %H:%M:%S')


class BaseOrder(APIBaseObjectModel):
    """
    Базовая модель фоновых и рекламных заказов.

    Содержит:
    - описание;
    - интервал вещания;
    - статус;
    - клиента;
    - плейлист;
    - дополнительные параметры.
    """

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Описание',
    )

    broadcast_interval = DateTimeRangeField(
        verbose_name='Интервал работы заказа',
        null=False,
        blank=True,
    )

    status = models.PositiveSmallIntegerField(
        choices=STATUSES,
        verbose_name='Статус',
        default=0,
    )

    client = models.ForeignKey(
        Nomenclature,
        related_name='%(class)ss',
        verbose_name='Рабочая станция',
        on_delete=models.DO_NOTHING,
    )

    playlist = models.ForeignKey(
        Playlist,
        related_name='%(class)ss',
        verbose_name='Плейлист',
        on_delete=models.DO_NOTHING,
    )

    parameters = models.JSONField(
        verbose_name='Параметры заказа',
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    def get_broadcast_start_local(self):
        """
        Возвращает локальное начало вещания строкой:

        YYYY-MM-DD HH:MM:SS
        """
        if not self.broadcast_interval:
            return None

        return _format_local_datetime(
            self.broadcast_interval.lower
        )

    def get_broadcast_end_local(self):
        """
        Возвращает локальное окончание вещания строкой:

        YYYY-MM-DD HH:MM:SS

        Для бессрочного диапазона возвращает None.
        """
        if not self.broadcast_interval:
            return None

        return _format_local_datetime(
            self.broadcast_interval.upper
        )

    @property
    def broadcast_start_local(self):
        """Начало вещания в локальном формате."""
        return self.get_broadcast_start_local()

    @property
    def broadcast_end_local(self):
        """Окончание вещания в локальном формате."""
        return self.get_broadcast_end_local()


class AdOrder(BaseOrder):
    """
    Рекламный заказ.

    broadcast_type:
        0 — по времени работы точки;
        1 — открытие + смещение;
        2 — закрытие - смещение;
        3 — конкретные часы;
        4 — с открытия до фиксированного часа;
        5 — с фиксированного часа до закрытия;
        6 — старт по событию.
    """

    slides = models.JSONField(
        verbose_name='Слайды',
        null=True,
        blank=True,
    )

    broadcast_type = models.PositiveSmallIntegerField(
        choices=BROADCAST_TYPES,
        verbose_name='Тип вещания',
    )

    class Meta:
        db_table = 'adorder'
        ordering = ('-created',)
        verbose_name = 'Рекламный заказ'
        verbose_name_plural = 'Рекламные заказы'


class BgOrder(BaseOrder):
    """
    Фоновый заказ.

    order_type:
        0 — музыка;
        1 — видео;
        2 — картинки;
        3 — бегущая строка.

    Бессрочный заказ используется как резервный плейлист, когда
    отсутствуют активные срочные заказы соответствующего типа.
    """

    order_type = models.PositiveSmallIntegerField(
        choices=ORDER_TYPES,
        verbose_name='Тип фона',
    )

    is_permanent = models.BooleanField(
        default=False,
        verbose_name='Бессрочный заказ',
        help_text=(
            'Если включено — заказ не имеет даты окончания и используется '
            'как резервный плейлист. Играет, когда нет активных заказов '
            'с указанными датами.'
        ),
    )

    class Meta:
        db_table = 'bgorder'
        ordering = ('-created',)
        verbose_name = 'Фоновый заказ'
        verbose_name_plural = 'Фоновые заказы'
