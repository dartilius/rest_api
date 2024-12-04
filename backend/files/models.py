from django.db import models
from django_minio_backend import MinioBackend
from rest_framework.exceptions import ValidationError

from api import APIBaseObjectModel
from api.constants import get_minio_client
from files.file_info import GetFileInfo

TYPES = {
    0: 'music',
    1: 'image',
    2: 'video',
    3: 'ticker',
    4: 'ad'
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
    return f'{TYPES[instance.type]}/{filename}'


class File(APIBaseObjectModel):
    """Файлы."""

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
        # добавляем это после фикса в джанге
        # https://github.com/django/django/pull/17723
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=['name'],
        #         name='unique_file_name',
        #         violation_error_message='Файл с таким названием уже существует',
        #         violation_error_code=400
        #     ),
        #     models.UniqueConstraint(
        #         fields=['hash'],
        #         name='unique_file_hash',
        #         violation_error_message='Файл с таким хешем уже существует',
        #         violation_error_code=400
        #     )
        # ]

    def save(self, *args, **kwargs):
        """
        Сборка информации о файле при его прогрузке на сервер.

        Имя берётся непосредственно с файла.
        Хэш суммы, размер и продолжительность вычисляются в отдельной функции.
        Суммированный хэш получается сложением md5 и sha256 хешей.
        """
        from api.constants import get_list_of_file_types
        types = get_list_of_file_types()
        file_type = TYPES[self.type]
        allowed_types: set = types[file_type]
        file = self.source.file
        self.name = file.name.split('/')[-1]
        extension = self.name.split('.')[-1]
        if extension not in allowed_types:
            self.delete()
            raise ValidationError(
                'Выбранный тип файла не соответствует его формату.\n'
                f'Для типа {file_type} допустимы следующие форматы:'
                f'{allowed_types}'
            )
        self.md5hash = GetFileInfo.get_md5(file)
        self.sha256hash = GetFileInfo.get_sha256(file)
        self.hash = f'{self.md5hash}{self.sha256hash}'
        self.length = GetFileInfo.get_length(file)
        self.size = GetFileInfo.get_file_size(file)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """При удалении файла с базы удаляем его также и в Минио."""
        from django.conf import settings

        minio_client = get_minio_client()
        minio_client.remove_object(
            settings.MINIO_MEDIA_FILES_BUCKET,
            f'{TYPES[self.type]}/{self.name}'
        )
        super().delete(*args, **kwargs)

    @property
    def url(self):
        """Ссылка для скачивания файла."""
        from datetime import timedelta as td
        client = get_minio_client(external=True)
        url = client.get_presigned_url(
            'GET',
            'local-media',
            f'{self.source}',
            expires=td(hours=2)
        )
        return url


class Playlist(APIBaseObjectModel):
    """Плейлисты."""

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Описание'
    )
    files = models.ManyToManyField(
        File,
        related_name='files',
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
                violation_error_message='Плейлист с таким названием '
                                        'уже существует'
            )
        ]
