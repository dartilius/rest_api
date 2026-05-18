# orders/models.py
"""
Модели для управления заказами.

БЕССРОЧНЫЕ ЗАКАЗЫ (is_permanent):
───────────────────────────────────────────────────────────────────────────────
Поле is_permanent (BooleanField) добавлено в базовый класс BaseOrder.

Когда is_permanent = True:
- Заказ не имеет даты окончания (broadcast_interval.upper может быть None)
- Используется как резервный плейлист
- Имеет низший приоритет при выборе плейлиста для воспроизведения

Когда is_permanent = False:
- Обычный срочный заказ с указанным интервалом вещания
- Имеет высокий приоритет при попадании в текущий период

ЛОГИКА ВЫБОРА ПЛЕЙЛИСТА НА КЛИЕНТЕ:
───────────────────────────────────────────────────────────────────────────────
1. Сначала проверяются срочные заказы (is_permanent=False)
   с датами, попадающими в текущий период
2. Если срочных заказов нет — используется бессрочный заказ
   (is_permanent=True) для соответствующего типа контента
3. Для каждого типа контента (музыка/видео/картинки) может быть
   только один активный бессрочный заказ
"""

from django.contrib.postgres.fields import DateTimeRangeField
from django.db import models

from api import APIBaseObjectModel
from nomenclatures.models import Nomenclature
from files.models import Playlist

ORDER_TYPES = {
    0: 'Фоновая музыка',
    1: 'Фоновые видео',
    2: 'Фоновые картинки',
    3: 'Бегущая строка'
}

STATUSES = {
    0: 'Ожидает эфира',
    1: 'В эфире',
    2: 'Завершён',
    3: 'Отменён',
    4: 'Ошибка'
}

BROADCAST_TYPES = {
    0: 'По времени работы точки',
    1: 'Начало работы + смещение по времени',
    2: 'Конец работы - смещение по времени',
    3: 'Конкретные часы',
    4: 'С открытия до фиксированного часа',
    5: 'С фиксированного часа до закрытия',
    6: 'Старт по событию'
}


class BaseOrder(APIBaseObjectModel):
    """
    Базовый класс для всех типов заказов.

    АТРИБУТЫ:
        description (str): Описание заказа (опционально)
        broadcast_interval (DateTimeRangeField): Интервал вещания
            Для бессрочных заказов может быть None или содержать только lower
        status (int): Статус заказа (0-4)
        client (ForeignKey): Рабочая станция (номенклатура)
        playlist (ForeignKey): Плейлист с файлами для воспроизведения
        parameters (JSON): Дополнительные параметры заказа
        is_permanent (bool): Флаг бессрочного заказа (новое поле)
    """

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Описание'
    )
    broadcast_interval = DateTimeRangeField(
        verbose_name='Интервал работы заказа',
        null=True,  # 🔥 Может быть NULL для бессрочных заказов
        blank=True
    )
    status = models.PositiveSmallIntegerField(
        choices=STATUSES,
        verbose_name='Статус',
        default=0
    )
    client = models.ForeignKey(
        Nomenclature,
        related_name='%(class)ss',
        verbose_name='Рабочая станция',
        on_delete=models.DO_NOTHING
    )
    playlist = models.ForeignKey(
        Playlist,
        related_name='%(class)ss',
        verbose_name='Плейлист',
        on_delete=models.DO_NOTHING
    )
    parameters = models.JSONField(
        verbose_name='Параметры заказа'
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class AdOrder(BaseOrder):
    """
    Рекламный заказ.

    Дополнительные атрибуты:
        slides (JSON): Слайды для рекламы (опционально)
        broadcast_type (int): Тип вещания (0-6)
    """

    slides = models.JSONField(
        verbose_name='Слайды',
        null=True,
        blank=True
    )
    broadcast_type = models.PositiveSmallIntegerField(
        choices=BROADCAST_TYPES,
        verbose_name='Тип вещания'
    )

    class Meta:
        db_table = 'adorder'
        ordering = ('-created',)
        verbose_name = 'Рекламный заказ'
        verbose_name_plural = 'Рекламные заказы'


class BgOrder(BaseOrder):
    """
    Фоновый заказ.

    Дополнительные атрибуты:
        order_type (int): Тип фона (0-3)
           0 - Фоновая музыка
           1 - Фоновые видео
           2 - Фоновые картинки
           3 - Бегущая строка
    """

    order_type = models.PositiveSmallIntegerField(
        choices=ORDER_TYPES,
        verbose_name='Тип фона'
    )

    # 🔥 НОВОЕ ПОЛЕ — Бессрочный заказ
    is_permanent = models.BooleanField(
        default=False,
        verbose_name='Бессрочный заказ',
        help_text=(
            'Если включено — заказ не имеет даты окончания и используется '
            'как резервный плейлист. Играет когда нет активных заказов с датами.'
        )
    )

    class Meta:
        db_table = 'bgorder'
        ordering = ('-created',)
        verbose_name = 'Фоновый заказ'
        verbose_name_plural = 'Фоновые заказы'