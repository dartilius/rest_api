"""
Модели для управления файлами, плейлистами и тегами.

ОПТИМИЗИРОВАННАЯ ВЕРСИЯ С ПОДДЕРЖКОЙ ПОДТИПОВ (опционально)
═══════════════════════════════════════════════════════════════════════════════════

ВАЖНО: Все изменения обратно совместимы!
- Поле subtype опционально (может быть NULL)
- Существующие файлы продолжают работать без изменений
- Логика заказов (orders) и репликаций (tasks) не меняется
- Типы файлов (type) остаются основными для определения compatibility
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


# ====================================================================================
# МОДУЛЬ 1: КОНСТАНТЫ (НЕ МЕНЯЕМ СУЩЕСТВУЮЩИЕ ТИПЫ!)
# ====================================================================================


TYPES = {
    0: 'music',
    1: 'video',
    2: 'image',
    3: 'ticker',
    4: 'ad'
}

TYPE_CHOICES = [(key, value) for key, value in TYPES.items()]

# ============================================================================
# ПОДТИПЫ ФАЙЛОВ - НОВОЕ ПОЛЕ (опционально, не влияет на существующую логику)
# ============================================================================

# ВНИМАНИЕ: Подтипы НЕ используются в заказах и репликациях!
# Заказы используют только поле type (0-4) для определения совместимости.
# Подтипы - это чисто информационное поле для удобства в админке.

SUBTYPES = {
    # Музыка (type=0) - только для отображения в админке
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

# Для валидации (используется только при сохранении файла)
SUBTYPES_MAPPING = {key: value['parent_type'] for key, value in SUBTYPES.items()}


# ====================================================================================
# МОДУЛЬ 2: ФУНКЦИЯ ДЛЯ ПУТИ (обновлена для поддержки подтипов, но обратно совместима)
# ====================================================================================

def media_path(instance, filename):
    """
    Генерирует путь для сохранения файла.
    
    ФОРМАТ:
        - С подтипом: {тип}/{подтип}/{имя_файла}
        - Без подтипа: {тип}/default/{имя_файла}
    
    ВАЖНО: Старые файлы без подтипа сохраняются в папку default,
    что не ломает существующие ссылки.
    """
    subtype_path = 'default'
    if hasattr(instance, 'subtype') and instance.subtype:
        subtype_info = SUBTYPES.get(instance.subtype, {})
        subtype_path = subtype_info.get('name', instance.subtype).lower().replace(' ', '_')
    
    return f'{TYPES[instance.type]}/{subtype_path}/{filename}'


# ====================================================================================
# МОДУЛЬ 3: МОДЕЛЬ ТЕГОВ (без изменений)
# ====================================================================================

class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name='Название', editable=False)
    color = ColorField(verbose_name='Цвет', blank=True, null=True)

    class Meta:
        db_table = 'tag'
        ordering = ('name',)
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


# ====================================================================================
# МОДУЛЬ 4: МОДЕЛЬ ФАЙЛА (ДОБАВЛЕНО ПОЛЕ SUBTYPE, ОСТАЛЬНОЕ БЕЗ ИЗМЕНЕНИЙ)
# ====================================================================================

class File(APIBaseObjectModel):
    """
    МОДЕЛЬ ФАЙЛА.
    
    ВАЖНО ДЛЯ РАЗРАБОТЧИКОВ:
    ──────────────────────────────────────────────────────────────────────────────
    • Поле subtype является ОПЦИОНАЛЬНЫМ (может быть NULL)
    • Существующие файлы продолжают работать без изменений
    • Заказы (AdOrder, BgOrder) используют ТОЛЬКО поле type (0-4)
    • Репликации (Task) используют ТОЛЬКО поле type для определения типа контента
    • Подтипы НЕ ВЛИЯЮТ на логику совместимости файлов с заказами
    """
    
    source = models.FileField(
        verbose_name='Файл',
        upload_to=media_path,
        storage=MinioBackend(bucket_name='local-media')
    )
    
    # Эти поля остаются без изменений
    md5hash = models.CharField(max_length=32, editable=False, verbose_name='MD5')
    sha256hash = models.CharField(max_length=64, editable=False, verbose_name='SHA256')
    hash = models.CharField(editable=False, max_length=96, unique=True)
    length = models.TimeField(editable=False, verbose_name='Продолжительность', blank=True, null=True)
    size = models.IntegerField(editable=False, verbose_name='Размер', default=0)
    type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES, verbose_name='Тип')
    tags = models.ManyToManyField(Tag, related_name='files', verbose_name='Тэги', blank=True)
    
    # НОВОЕ ПОЛЕ: подтип (опционально, не влияет на логику заказов)
    subtype = models.CharField(
        max_length=50,
        choices=SUBTYPE_CHOICES,
        blank=True,
        null=True,
        verbose_name='Подтип',
        help_text='Детальная классификация файла (только для информации в админке)'
    )
    
    # name - будет добавлен в save() как раньше
    
    class Meta:
        db_table = 'file'
        ordering = ('-created',)
        verbose_name = 'Файл'
        verbose_name_plural = 'Файлы'
        indexes = [
            models.Index(fields=['hash'], name='file_hash_idx'),
            models.Index(fields=['type'], name='file_type_idx'),
            models.Index(fields=['subtype'], name='file_subtype_idx'),  # новый индекс
            models.Index(fields=['is_active'], name='file_active_idx'),
        ]
    
    def save(self, *args, **kwargs):
        """
        Сохранение файла.
        
        ВАЖНО: Логика сохранения НЕ ИЗМЕНЕНА!
        Добавлена только валидация подтипа (опционально).
        """
        from api.constants import get_list_of_file_types
        
        if not self.source:
            raise ValidationError('Файл не был передан')
        
        file = self.source.file
        
        # Сохраняем имя файла (как было)
        self.name = os.path.basename(file.name)
        filename, extension = os.path.splitext(self.name)
        
        # Проверка расширения (без изменений)
        if extension:
            extension = extension[1:].lower()
        
        types = get_list_of_file_types()
        file_type = TYPES[self.type]
        allowed_types = types[file_type]
        
        if extension and extension not in allowed_types:
            raise ValidationError(
                f'Выбранный тип файла не соответствует его формату.\n'
                f'Для типа "{file_type}" допустимы следующие форматы: {allowed_types}'
            )
        
        # Вычисление хэшей (без изменений)
        self.md5hash = GetFileInfo.get_md5(file)
        self.sha256hash = GetFileInfo.get_sha256(file)
        self.hash = f'{self.md5hash}{self.sha256hash}'
        
        # Вычисление длины (без изменений)
        if self.type in [0, 1]:
            self.length = GetFileInfo.get_length(file)
        else:
            self.length = None
        
        # Вычисление размера (без изменений)
        self.size = GetFileInfo.get_file_size(file)
        
        # НОВОЕ: валидация подтипа (только если указан)
        if self.subtype:
            expected_type = SUBTYPES_MAPPING.get(self.subtype)
            if expected_type is not None and expected_type != self.type:
                subtype_name = SUBTYPES.get(self.subtype, {}).get('name', self.subtype)
                raise ValidationError({
                    'subtype': f'Подтип "{subtype_name}" не соответствует типу файла "{TYPES[self.type]}".'
                })
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Мягкое удаление (без изменений)"""
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
        """Ссылка на файл (без изменений)"""
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
        """Иконка подтипа (только для отображения в админке)"""
        if self.subtype:
            return SUBTYPES.get(self.subtype, {}).get('icon', '📄')
        return '📄'
    
    @property
    def subtype_display(self):
        """Название подтипа (только для отображения в админке)"""
        if self.subtype:
            return SUBTYPES.get(self.subtype, {}).get('name', self.subtype)
        return '-'
    
    def __str__(self):
        return f'{self.name} ({TYPES[self.type]})'


# ====================================================================================
# МОДУЛЬ 5: МОДЕЛЬ ПЛЕЙЛИСТА (БЕЗ ИЗМЕНЕНИЙ)
# ====================================================================================

class Playlist(APIBaseObjectModel):
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    files = models.ManyToManyField(File, related_name='playlists', verbose_name='Файлы')

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
        return self.files.count()

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