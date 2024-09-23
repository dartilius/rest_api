from uuid import uuid4

from django.db import models
from django_minio_backend import MinioBackend

from files.file_info import GetFileInfo
from users.models import CustomUser

TYPES = {
    0: 'ad',
    1: 'music',
    2: 'image',
    3: 'video',
    4: 'ticker'
}


class Tag(models.Model):
    """Тэги."""

    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Название'
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'tag'
        ordering = ('name',)
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэг'


def media_path(instance, filename):
    return f'{TYPES[instance.file_type]}/{filename}'


class File(models.Model):
    """Файлы."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
        verbose_name='Уникальный идентификатор'
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Наименование',
        unique=True
    )
    owner = models.ForeignKey(
        CustomUser,
        related_name='files',
        blank=True,
        null=True,
        verbose_name='Кто загрузил',
        on_delete=models.SET_NULL
    )
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
        max_length=256,
        editable=False,
        verbose_name='SHA256'
    )
    hash = models.CharField(
        editable=False,
        max_length=288,
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
        default=0,
        verbose_name='Размер'
    )
    file_type = models.PositiveSmallIntegerField(
        choices=TYPES,
        verbose_name='Тип'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='files',
        verbose_name='Тэги'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        db_table = 'file'
        ordering = ('-created',)
        verbose_name = 'Файл'
        verbose_name_plural = 'Файлы'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Сборка информации о файле при его прогрузке на сервер.

        Имя берётся непосредственно с файла.
        Хэш суммы, размер и продолжительность вычисляются в отдельной функции.
        Суммированный хэш получается сложением md5 и sha256 хешей.
        """
        file = self.source.file
        self.name = file.name.split('/')[-1]
        self.md5hash = GetFileInfo.get_md5(file)
        self.sha256hash = GetFileInfo.get_sha256(file)
        self.hash = f'{self.md5hash}{self.sha256hash}'
        self.length = GetFileInfo.get_length(file)
        self.size = GetFileInfo.get_file_size(file)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """При удалении файла с базы удаляем его также и в Минио."""
        from minio import Minio
        from django.conf import settings

        minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_HTTPS,
            cert_check=settings.MINIO_USE_HTTPS
        )
        minio_client.remove_object(
            settings.MINIO_MEDIA_FILES_BUCKET,
            f'{TYPES[self.file_type]}/{self.name}'
        )
        super().delete(*args, **kwargs)


class Playlist(models.Model):
    """Плейлисты."""

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
    owner = models.ForeignKey(
        CustomUser,
        related_name='playlists',
        verbose_name='Создатель',
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    files = models.ManyToManyField(
        File,
        related_name='files',
        verbose_name='Файлы'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        db_table = 'playlist'
        ordering = ('-created',)
        verbose_name = 'Плейлист'
        verbose_name_plural = 'Плейлисты'

    def __str__(self):
        return self.name
