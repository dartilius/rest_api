from django.contrib.postgres.fields import HStoreField
# from django.core.exceptions import ValidationError
from django.db import models

from nomenclatures.models import NomenclatureGroup
from users.models import CustomUser
from files.models import Playlist, File

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


# class Mediaplan(models.Model):
#     """Медиаплан."""
#
#     name = models.CharField()
#     type = models.BooleanField(
#         choices={0: 'Рекламный',
#                  1: 'Фоновый'},
#         verbose_name='Тип',
#         default=0
#     )
#     description = models.TextField(
#         null=True,
#         blank=True,
#         verbose_name='Описание'
#     )
#     broadcast_interval = DateTimeRangeField(
#         verbose_name='Интервал работы заказа'
#     )
#     created = models.DateTimeField(
#         verbose_name='Дата создания',
#         auto_now_add=True
#     )
#
#     class Meta:
#         abstract = True
#
#
# class AdMediaplan(Mediaplan):
#     """."""
#
#     parameters = ('times_in_hour',
#                   'weight_val',
#                   'event_val',
#                   'ad_action',
#                   'start_time',
#                   'end_time',
#                   'timedelta_val')
#
#     group = models.ForeignKey(
#         NomenclatureGroup,
#         verbose_name='group',
#         related_name='ad_mediaplans',
#         on_delete=models.DO_NOTHING
#     )
#     playlist = models.ForeignKey(
#         Playlist,
#         verbose_name='playlist',
#         related_name='ad_mediaplans',
#         on_delete=models.DO_NOTHING,
#         blank=True,
#         null=True
#     )
#     file = models.ForeignKey(
#         File,
#         verbose_name='Файл',
#         related_name='ad_mediaplans',
#         on_delete=models.DO_NOTHING,
#         blank=True,
#         null=True
#     )
#
#     def clean(self):
#         if self.playlist and self.file:
#             raise ValidationError(
#                 'Должно быть заполнено что-то одно - плейлист или файл.')
#         elif not (self.playlist or self.file):
#             raise ValidationError(
#                 'Необходимо добавить плейлист или файл.')
#
#
# class BgMediaplan(Mediaplan):
#     """."""
#
#     group = models.ForeignKey(
#         NomenclatureGroup,
#         verbose_name='group',
#         related_name='bg_mediaplans',
#         on_delete=models.DO_NOTHING
#     )
#     playlist = models.ForeignKey(
#         Playlist,
#         verbose_name='playlist',
#         related_name='bg_mediaplans',
#         on_delete=models.DO_NOTHING
#     )


class BaseOrder(models.Model):
    """Заказ."""

    name = models.CharField(
        max_length=255,
        verbose_name='Название'
    )
    status = models.PositiveSmallIntegerField(
        choices=STATUSES,
        verbose_name='Статус',
        default=0
    )
    created = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class AdOrder(BaseOrder):
    """Рекламный заказ."""

    owner = models.ForeignKey(
        CustomUser,
        verbose_name='Создатель',
        related_name='ad_orders',
        on_delete=models.DO_NOTHING
    )
    group = models.ForeignKey(
        NomenclatureGroup,
        related_name='ad_orders',
        verbose_name='Группа номенклатур',
        on_delete=models.DO_NOTHING
    )
    playlist = models.ForeignKey(
        Playlist,
        verbose_name='Ролики',
        related_name='ad_orders',
        on_delete=models.DO_NOTHING
    )
    slides = models.ManyToManyField(
        File,
        verbose_name='Слайды',
        related_name='slides_orders',
        blank=True
    )
    broadcast_type = models.PositiveSmallIntegerField(
        choices=BROADCAST_TYPES,
        default=0,
        verbose_name='Тип вещания'
    )
    parameters = HStoreField(
        default=dict,
        verbose_name='Параметры заказа'
    )
    # mediaplan = models.ForeignKey(
    #     AdMediaplan,
    #     verbose_name='Медиаплан',
    #     related_name='orders',
    #     on_delete=models.DO_NOTHING
    # )

    class Meta:
        db_table = 'ad_order'
        ordering = ('-created',)
        verbose_name = 'Рекламный заказ'
        verbose_name_plural = 'Реклама'


class BgOrder(BaseOrder):
    """Фоновый заказ."""

    owner = models.ForeignKey(
        CustomUser,
        verbose_name='Создатель',
        related_name='bg_orders',
        on_delete=models.DO_NOTHING
    )
    group = models.ForeignKey(
        NomenclatureGroup,
        related_name='bg_orders',
        verbose_name='Группа номенклатур',
        on_delete=models.DO_NOTHING
    )
    playlist = models.ForeignKey(
        Playlist,
        related_name='bg_orders',
        verbose_name='Плейлист',
        on_delete=models.DO_NOTHING
    )
    order_type = models.PositiveSmallIntegerField(
        choices=ORDER_TYPES,
        verbose_name='Тип фона'
    )
    # mediaplan = models.ForeignKey(
    #     Mediaplan,
    #     verbose_name='Медиаплан',
    #     related_name='bg_orders',
    #     on_delete=models.DO_NOTHING
    # )

    class Meta:
        db_table = 'bg_order'
        ordering = ('-created',)
        verbose_name = 'Фоновый заказ'
        verbose_name_plural = 'Фон'
