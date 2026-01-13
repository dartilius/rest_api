from colorfield.fields import ColorField
from django.db import models
from django_minio_backend import MinioBackend
from rest_framework.exceptions import ValidationError
import os

from api import APIBaseObjectModel
from api.constants import get_minio_client
from files.file_info import GetFileInfo

TYPES = {
    0: 'music',
    1: 'video',
    2: 'image',
    3: 'ticker',
    4: 'ad'
}


class Tag(models.Model):
    """Тэги."""

    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Название',
        editable=False
    )
    color = ColorField(
        verbose_name='Цвет',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'tag'
        ordering = ('name',)
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'  # Исправлено с 'Тэг' на 'Тэги'


def media_path(instance, filename):
    """Генерирует путь для сохранения файла в бакете MinIO."""
    return f'{TYPES[instance.type]}/{filename}'


class File(APIBaseObjectModel):
    """Файлы."""

    # КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Явно указываем MinioBackend с бакетом
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
        choices=TYPES,
        verbose_name='Тип'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='files',
        verbose_name='Тэги',
        blank=True
    )

    class Meta:
        db_table = 'file'
        ordering = ('-created',)
        verbose_name = 'Файл'
        verbose_name_plural = 'Файлы'

    def save(self, *args, **kwargs):
        """
        Сборка информации о файле при его прогрузке на сервер.
        """
        from api.constants import get_list_of_file_types

        # Проверяем, есть ли файл для загрузки
        if not self.source:
            raise ValidationError('Файл не был передан')

        types = get_list_of_file_types()
        file_type = TYPES[self.type]
        allowed_types = types[file_type]

        # Получаем информацию о файле
        file = self.source.file
        self.name = os.path.basename(file.name)
        filename, extension = os.path.splitext(self.name)

        # Проверяем расширение файла
        if extension:
            extension = extension[1:].lower()  # Убираем точку и приводим к нижнему регистру

        if extension not in allowed_types:
            raise ValidationError(
                f'Выбранный тип файла не соответствует его формату.\n'
                f'Для типа "{file_type}" допустимы следующие форматы: {allowed_types}'
            )

        # Рассчитываем хэши и размер
        self.md5hash = GetFileInfo.get_md5(file)
        self.sha256hash = GetFileInfo.get_sha256(file)
        self.hash = f'{self.md5hash}{self.sha256hash}'
        self.length = GetFileInfo.get_length(file)
        self.size = GetFileInfo.get_file_size(file)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """При удалении файла с базы удаляем его также и в MinIO."""
        import logging

        # Сохраняем путь к файлу до удаления
        file_path = str(self.source)

        # Сначала удаляем запись из БД
        super().delete(*args, **kwargs)

        # Затем пытаемся удалить файл из MinIO
        try:
            minio_client = get_minio_client()
            # Явное указание бакета
            minio_client.remove_object('local-media', file_path)
        except Exception as e:
            # Логируем ошибку, но не поднимаем исключение
            logger = logging.getLogger(__name__)
            logger.warning(f'Не удалось удалить файл из MinIO: {file_path}. Ошибка: {e}')

    @property
    def url(self):
        """Ссылка для скачивания файла. Использует явные параметры."""
        from datetime import timedelta as td

        client = get_minio_client(external=True)

        # Явное указание бакета и пути к файлу
        url = client.get_presigned_url(
            'GET',
            'local-media',  # Бакет из MinioBackend
            str(self.source),  # Полный путь к файлу
            expires=td(hours=2)
        )
        return url

    def __str__(self):
        return f'{self.name} ({TYPES[self.type]})'


class Playlist(APIBaseObjectModel):
    """Плейлисты."""

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Описание'
    )
    files = models.ManyToManyField(
        File,
        related_name='playlists',  # Исправлено с 'files' на 'playlists' для ясности
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