# files/models.py - ПОЛНЫЙ ФАЙЛ
"""
Модели для управления файлами, плейлистами и тегами.

ОПТИМИЗИРОВАННАЯ ВЕРСИЯ С ПОДДЕРЖКОЙ ПОДТИПОВ (опционально)
═══════════════════════════════════════════════════════════════════════════════════

ВАЖНО: Все изменения обратно совместимы!
- Поле subtype опционально (может быть NULL)
- Существующие файлы продолжают работать без изменений
- Логика заказов (orders) и репликаций (tasks) не меняется
- Типы файлов (type) остаются основными для определения compatibility

ТИПЫ ФАЙЛОВ (type):
    0 - Музыка (music)
    1 - Видео (video)
    2 - Изображения (image)
    3 - Бегущая строка (ticker)
    4 - Реклама (ad)

ПОДТИПЫ (subtype):
    Опциональная детальная классификация файлов.
    Используется ТОЛЬКО для отображения в админке.
    НЕ влияет на логику заказов и репликаций.

СТРУКТУРА ХРАНЕНИЯ:
    Файлы хранятся в MinIO (S3-совместимое облачное хранилище).
    Путь формируется по шаблону:
        {тип}/{подтип|default}/{имя_файла}
"""

import os
import logging

from colorfield.fields import ColorField
from django.db import models
from django.core.exceptions import ValidationError
from django_minio_backend import MinioBackend

from api import APIBaseObjectModel
from api.constants import get_minio_client
from files.file_info import GetFileInfo

# ═══════════════════════════════════════════════════════════════════════════════
# КОНСТАНТЫ ТИПОВ ФАЙЛОВ
# ═══════════════════════════════════════════════════════════════════════════════

TYPES = {
    0: 'music',
    1: 'video',
    2: 'image',
    3: 'ticker',
    4: 'ad'
}

TYPE_CHOICES = [(key, value) for key, value in TYPES.items()]

# ═══════════════════════════════════════════════════════════════════════════════
# ПОДТИПЫ ФАЙЛОВ (опционально, только для админки)
# ═══════════════════════════════════════════════════════════════════════════════

SUBTYPES = {
    # Музыка (type=0)
    'music_pop': {'name': 'Поп-музыка', 'icon': '🎤', 'parent_type': 0},
    'music_rock': {'name': 'Рок', 'icon': '🎸', 'parent_type': 0},
    'music_jazz': {'name': 'Джаз', 'icon': '🎷', 'parent_type': 0},
    'music_classical': {'name': 'Классика', 'icon': '🎻', 'parent_type': 0},
    'music_electronic': {'name': 'Электронная', 'icon': '🎧', 'parent_type': 0},
    'music_hiphop': {'name': 'Хип-хоп', 'icon': '🎙️', 'parent_type': 0},

    # Видео (type=1)
    'video_short': {'name': 'Короткое видео', 'icon': '📱', 'parent_type': 1},
    'video_long': {'name': 'Длинное видео', 'icon': '📺', 'parent_type': 1},
    'video_promo': {'name': 'Промо-ролик', 'icon': '📢', 'parent_type': 1},
    'video_animation': {'name': 'Анимация', 'icon': '🎬', 'parent_type': 1},

    # Изображения (type=2)
    'image_photo': {'name': 'Фотография', 'icon': '📸', 'parent_type': 2},
    'image_illustration': {'name': 'Иллюстрация', 'icon': '🎨', 'parent_type': 2},
    'image_logo': {'name': 'Логотип', 'icon': '🏷️', 'parent_type': 2},
    'image_banner': {'name': 'Баннер', 'icon': '🖼️', 'parent_type': 2},
    'image_background': {'name': 'Фон', 'icon': '🌈', 'parent_type': 2},

    # Бегущая строка (type=3)
    'ticker_text': {'name': 'Текстовая строка', 'icon': '📝', 'parent_type': 3},
    'ticker_animated': {'name': 'Анимированная строка', 'icon': '✨', 'parent_type': 3},

    # Реклама (type=4)
    'ad_banner': {'name': 'Баннерная реклама', 'icon': '📊', 'parent_type': 4},
    'ad_video': {'name': 'Видеореклама', 'icon': '📺', 'parent_type': 4},
    'ad_audio': {'name': 'Аудиореклама', 'icon': '🎵', 'parent_type': 4},
}

SUBTYPE_CHOICES = [(key, value['name']) for key, value in SUBTYPES.items()]
SUBTYPES_MAPPING = {key: value['parent_type'] for key, value in SUBTYPES.items()}


# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════════════════════

def media_path(instance, filename):
    """
    Генерирует путь для сохранения файла в MinIO.

    ФОРМАТ ПУТИ:
        {тип}/{подтип|default}/{имя_файла}

    ПРИМЕРЫ:
        music/music_pop/song.mp3
        video/default/video.mp4
        image/image_banner/banner.jpg

    Для файлов без подтипа используется папка 'default'.
    """
    subtype_path = 'default'
    if hasattr(instance, 'subtype') and instance.subtype:
        subtype_info = SUBTYPES.get(instance.subtype, {})
        subtype_path = subtype_info.get('name', instance.subtype).lower().replace(' ', '_')

    return f'{TYPES[instance.type]}/{subtype_path}/{filename}'


# ═══════════════════════════════════════════════════════════════════════════════
# МОДЕЛИ
# ═══════════════════════════════════════════════════════════════════════════════

class Tag(models.Model):
    """
    Тег для категоризации файлов.

    АТРИБУТЫ:
        name (str): Название тега (уникальное, до 255 символов)
        color (str): Цвет в формате HEX (опционально)

    ИСПОЛЬЗОВАНИЕ:
        Теги используются для группировки и фильтрации файлов.
        Не влияют на логику заказов и репликаций.
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Название'
    )
    color = ColorField(
        verbose_name='Цвет',
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'tag'
        ordering = ('name',)
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class File(APIBaseObjectModel):
    """
    Модель файла.

    АТРИБУТЫ:
        source (FileField): Файл в MinIO
        md5hash (str): MD5 хэш (32 символа)
        sha256hash (str): SHA256 хэш (64 символа)
        hash (str): Комбинированный хэш (md5 + sha256, 96 символов, уникальный)
        length (TimeField): Продолжительность аудио/видео
        size (int): Размер в байтах
        type (int): Тип файла (0-4)
        subtype (str): Подтип (опционально, только для админки)
        tags (ManyToMany): Теги файла

    ВАЖНО:
        - Поле subtype ОПЦИОНАЛЬНО (может быть NULL)
        - Заказы используют ТОЛЬКО поле type
        - Подтипы НЕ влияют на логику совместимости
    """

    source = models.FileField(
        verbose_name='Файл',
        upload_to=media_path,
        storage=MinioBackend(bucket_name='local-media')
    )

    md5hash = models.CharField(
        max_length=32,
        editable=False,
        verbose_name='MD5'
    )
    sha256hash = models.CharField(
        max_length=64,
        editable=False,
        verbose_name='SHA256'
    )
    hash = models.CharField(
        editable=False,
        max_length=96,
        unique=True
    )
    length = models.TimeField(
        editable=False,
        verbose_name='Продолжительность',
        blank=True,
        null=True
    )
    size = models.IntegerField(
        editable=False,
        verbose_name='Размер',
        default=0
    )
    type = models.PositiveSmallIntegerField(
        choices=TYPE_CHOICES,
        verbose_name='Тип'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='files',
        verbose_name='Тэги',
        blank=True
    )
    subtype = models.CharField(
        max_length=50,
        choices=SUBTYPE_CHOICES,
        blank=True,
        null=True,
        verbose_name='Подтип',
        help_text='Детальная классификация (только для админки)'
    )

    class Meta:
        db_table = 'file'
        ordering = ('-created',)
        verbose_name = 'Файл'
        verbose_name_plural = 'Файлы'
        indexes = [
            models.Index(fields=['hash'], name='file_hash_idx'),
            models.Index(fields=['type'], name='file_type_idx'),
            models.Index(fields=['subtype'], name='file_subtype_idx'),
            models.Index(fields=['is_active'], name='file_active_idx'),
        ]

    def save(self, *args, **kwargs):
        """
        Сохранение файла с автоматическим вычислением хэшей и длительности.

        ПОРЯДОК ДЕЙСТВИЙ:
        1. Проверка наличия файла
        2. Извлечение имени и расширения
        3. Проверка соответствия расширения типу файла
        4. Вычисление MD5 и SHA256 хэшей
        5. Комбинирование хэшей
        6. Вычисление длительности (для аудио/видео)
        7. Вычисление размера
        8. Валидация подтипа (если указан)
        """
        from api.constants import get_list_of_file_types

        if not self.source:
            raise ValidationError('Файл не был передан')

        file = self.source.file

        # Имя файла
        self.name = os.path.basename(file.name)
        filename, extension = os.path.splitext(self.name)

        # Проверка расширения
        if extension:
            extension = extension[1:].lower()

        types = get_list_of_file_types()
        file_type = TYPES[self.type]
        allowed_types = types[file_type]

        if extension and extension not in allowed_types:
            raise ValidationError(
                f'Выбранный тип файла не соответствует его формату.\n'
                f'Для типа "{file_type}" допустимы форматы: {allowed_types}'
            )

        # Хэши
        self.md5hash = GetFileInfo.get_md5(file)
        self.sha256hash = GetFileInfo.get_sha256(file)
        self.hash = f'{self.md5hash}{self.sha256hash}'

        # Длительность (только для аудио/видео)
        if self.type in [0, 1]:
            self.length = GetFileInfo.get_length(file)
        else:
            self.length = None

        # Размер
        self.size = GetFileInfo.get_file_size(file)

        # Валидация подтипа
        if self.subtype:
            expected_type = SUBTYPES_MAPPING.get(self.subtype)
            if expected_type is not None and expected_type != self.type:
                subtype_name = SUBTYPES.get(self.subtype, {}).get('name', self.subtype)
                raise ValidationError({
                    'subtype': f'Подтип "{subtype_name}" не соответствует типу файла "{TYPES[self.type]}".'
                })

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Мягкое удаление файла.

        Файл не удаляется физически, а помечается как неактивный (is_active=False).
        Также удаляется из MinIO для освобождения места.
        """
        logger = logging.getLogger(__name__)

        file_path = str(self.source)
        self.is_active = False
        self.save(update_fields=['is_active', 'modified'])

        try:
            minio_client = get_minio_client()
            minio_client.remove_object('local-media', file_path)
            logger.info(f'Файл удален из MinIO: {file_path}')
        except Exception as e:
            logger.warning(f'Не удалось удалить файл из MinIO: {file_path}. Ошибка: {e}')

    @property
    def url(self):
        """
        Генерирует временную ссылку на файл в MinIO.

        Ссылка действительна 2 часа.
        Результат кэшируется в атрибуте _cached_url до конца жизни объекта.
        """
        from datetime import timedelta as td

        if hasattr(self, '_cached_url') and self._cached_url:
            return self._cached_url

        client = get_minio_client(external=True)
        url = client.get_presigned_url(
            'GET',
            'local-media',
            str(self.source),
            expires=td(hours=2)
        )

        self._cached_url = url
        return url

    @property
    def subtype_icon(self):
        """Возвращает иконку подтипа для отображения в админке."""
        if self.subtype:
            return SUBTYPES.get(self.subtype, {}).get('icon', '📄')
        return '📄'

    @property
    def subtype_display(self):
        """Возвращает название подтипа для отображения в админке."""
        if self.subtype:
            return SUBTYPES.get(self.subtype, {}).get('name', self.subtype)
        return '-'

    def __str__(self):
        return f'{self.name} ({TYPES[self.type]})'


class Playlist(APIBaseObjectModel):
    """
    Модель плейлиста.

    АТРИБУТЫ:
        description (str): Описание плейлиста (опционально)
        files (ManyToMany): Файлы плейлиста

    ОГРАНИЧЕНИЯ:
        - Название плейлиста уникально
        - Все файлы в плейлисте должны быть одного типа

    ИСПОЛЬЗОВАНИЕ:
        Плейлисты используются в заказах (AdOrder, BgOrder) для указания
        набора файлов для воспроизведения.
    """
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Описание'
    )
    files = models.ManyToManyField(
        File,
        related_name='playlists',
        verbose_name='Файлы'
    )

    class Meta:
        db_table = 'playlist'
        ordering = ('-created',)
        verbose_name = 'Плейлист'
        verbose_name_plural = 'Плейлисты'
        constraints = [
            models.UniqueConstraint(
                fields=['name'],
                name='unique_playlist_name',
                violation_error_message='Плейлист с таким названием уже существует'
            )
        ]

    def __str__(self):
        return self.name

    @property
    def files_count(self):
        """Возвращает количество файлов в плейлисте."""
        return self.files.count()

    # @property
    # def files_count(self):
    #     return self.files.count()

# from colorfield.fields import ColorField
# from django.db import models
# from django_minio_backend import MinioBackend
# from rest_framework.exceptions import ValidationError
# import os

# from api import APIBaseObjectModel
# from api.constants import get_minio_client
# from files.file_info import GetFileInfo

# TYPES = {
#     0: 'music',
#     1: 'video',
#     2: 'image',
#     3: 'ticker',
#     4: 'ad'
# }


# class Tag(models.Model):
#     """Тэги."""

#     name = models.CharField(
#         max_length=255,
#         unique=True,
#         verbose_name='Название',
#         editable=False
#     )
#     color = ColorField(
#         verbose_name='Цвет',
#         blank=True,
#         null=True
#     )

#     def __str__(self):
#         return self.name

#     class Meta:
#         db_table = 'tag'
#         ordering = ('name',)
#         verbose_name = 'Тэг'
#         verbose_name_plural = 'Тэги'  # Исправлено с 'Тэг' на 'Тэги'


# def media_path(instance, filename):
#     """Генерирует путь для сохранения файла в бакете MinIO."""
#     return f'{TYPES[instance.type]}/{filename}'


# class File(APIBaseObjectModel):
#     """Файлы."""

#     # КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Явно указываем MinioBackend с бакетом
#     source = models.FileField(
#         verbose_name='Файл',
#         upload_to=media_path,
#         storage=MinioBackend(bucket_name='local-media')
#     )
#     md5hash = models.CharField(
#         max_length=32,
#         editable=False,
#         verbose_name='MD5'
#     )
#     sha256hash = models.CharField(
#         max_length=64,
#         editable=False,
#         verbose_name='SHA256'
#     )
#     hash = models.CharField(
#         editable=False,
#         max_length=96,
#         unique=True
#     )
#     length = models.TimeField(
#         editable=False,
#         verbose_name='Продолжительность',
#         blank=True,
#         null=True
#     )
#     size = models.IntegerField(
#         editable=False,
#         verbose_name='Размер',
#         default=0
#     )
#     type = models.PositiveSmallIntegerField(
#         choices=TYPES,
#         verbose_name='Тип'
#     )
#     tags = models.ManyToManyField(
#         Tag,
#         related_name='files',
#         verbose_name='Тэги',
#         blank=True
#     )

#     class Meta:
#         db_table = 'file'
#         ordering = ('-created',)
#         verbose_name = 'Файл'
#         verbose_name_plural = 'Файлы'

#     def save(self, *args, **kwargs):
#         """
#         Сборка информации о файле при его прогрузке на сервер.
#         """
#         from api.constants import get_list_of_file_types

#         # Проверяем, есть ли файл для загрузки
#         if not self.source:
#             raise ValidationError('Файл не был передан')

#         types = get_list_of_file_types()
#         file_type = TYPES[self.type]
#         allowed_types = types[file_type]

#         # Получаем информацию о файле
#         file = self.source.file
#         self.name = os.path.basename(file.name)
#         filename, extension = os.path.splitext(self.name)

#         # Проверяем расширение файла
#         if extension:
#             extension = extension[1:].lower()  # Убираем точку и приводим к нижнему регистру

#         if extension not in allowed_types:
#             raise ValidationError(
#                 f'Выбранный тип файла не соответствует его формату.\n'
#                 f'Для типа "{file_type}" допустимы следующие форматы: {allowed_types}'
#             )

#         # Рассчитываем хэши и размер
#         self.md5hash = GetFileInfo.get_md5(file)
#         self.sha256hash = GetFileInfo.get_sha256(file)
#         self.hash = f'{self.md5hash}{self.sha256hash}'
#         self.length = GetFileInfo.get_length(file)
#         self.size = GetFileInfo.get_file_size(file)

#         super().save(*args, **kwargs)

#     def delete(self, *args, **kwargs):
#         """При удалении файла с базы удаляем его также и в MinIO."""
#         import logging

#         # Сохраняем путь к файлу до удаления
#         file_path = str(self.source)

#         # Сначала удаляем запись из БД
#         super().delete(*args, **kwargs)

#         # Затем пытаемся удалить файл из MinIO
#         try:
#             minio_client = get_minio_client()
#             # Явное указание бакета
#             minio_client.remove_object('local-media', file_path)
#         except Exception as e:
#             # Логируем ошибку, но не поднимаем исключение
#             logger = logging.getLogger(__name__)
#             logger.warning(f'Не удалось удалить файл из MinIO: {file_path}. Ошибка: {e}')

#     @property
#     def url(self):
#         """Ссылка для скачивания файла. Использует явные параметры."""
#         from datetime import timedelta as td

#         client = get_minio_client(external=True)

#         # Явное указание бакета и пути к файлу
#         url = client.get_presigned_url(
#             'GET',
#             'local-media',  # Бакет из MinioBackend
#             str(self.source),  # Полный путь к файлу
#             expires=td(hours=2)
#         )
#         return url

#     def __str__(self):
#         return f'{self.name} ({TYPES[self.type]})'


# class Playlist(APIBaseObjectModel):
#     """Плейлисты."""

#     description = models.TextField(
#         blank=True,
#         null=True,
#         verbose_name='Описание'
#     )
#     files = models.ManyToManyField(
#         File,
#         related_name='playlists',  # Исправлено с 'files' на 'playlists' для ясности
#         verbose_name='Файлы'
#     )

#     class Meta:
#         db_table = 'playlist'
#         ordering = ('-created',)
#         verbose_name = 'Плейлист'
#         verbose_name_plural = 'Плейлисты'
#         constraints = [
#             models.UniqueConstraint(
#                 fields=['name'],
#                 name='unique_playlist_name',
#                 violation_error_message='Плейлист с таким названием уже существует'
#             )
#         ]

#     def __str__(self):
#         return self.name
