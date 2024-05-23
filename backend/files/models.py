from uuid import uuid4

from django.db import models
from django_minio_backend import MinioBackend

from files.file_info import GetFileInfo
from users.models import CustomUser

TYPES = {
    0: 'Реклама',
    1: 'Музыка',
    2: 'Кртинка фон',
    3: 'Видео фон',
    4: 'Бегущая строка'
}


class Tag(models.Model):
    """Тэги."""

    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Название'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Слаг',
        max_length=200,
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'tag'
        ordering = ('name',)
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэг'


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
        upload_to='downloaded_files/source/',
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
        default='00:00:00',
        verbose_name='Продолжительность'
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
        file = self.source.file
        self.md5hash = GetFileInfo.get_md5(file)
        self.sha256hash = GetFileInfo.get_sha256(file)
        self.hash = f'{self.md5hash}{self.sha256hash}'
        self.length = GetFileInfo.get_length(file)
        self.size = GetFileInfo.get_file_size(file)
        super().save(*args, **kwargs)


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
