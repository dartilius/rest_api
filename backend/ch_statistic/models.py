# from clickhouse_backend import models
#
#
# class Stat(models.ClickhouseModel):
#     """Базовая статистика."""
#
#     created = models.DateTime64Field(
#         auto_now_add=True,
#         verbose_name='Запись создана'
#     )
#     played = models.DateTime64Field(
#         verbose_name='Когда было проиграно'
#     )
#     md5 = models.CharField(
#         max_length=32,
#         verbose_name='Контрольная сумма'
#     )
#     # client = models.UInt16Field(verbose_name='Номенклатура') # погуглить можно ли fk сделать и uuid поле
#     length = models.TimeField(
#         verbose_name='Хронометраж'
#     )
#     # file_id = models.UInt16Field(verbose_name='ID файла') # тот же fk и uuid
#
#
# class AD(Stat):
#     """Статистика рекламы."""
#
#     ad_block = models.TimeField(
#         verbose_name='Блок выхода в эфир'
#     )
#
# class Music(Stat):
#     """Статистика музыки."""
#
#
# class Image(Stat):
#     """Статистика фоновых картинок."""
#
#
# class Video(Stat):
#     """Статистика фоновых видео."""
#
#
# class Ticker(Stat):
#     """Статистика бегущей строки."""
