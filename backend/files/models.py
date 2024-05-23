from uuid import uuid4

from django.db import models
from django_minio_backend import MinioBackend

from files.file_info import GetFileInfo
from users.models import User

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
        verbose_name='Наименование'
    )
    # сбда просится slug

    def __str__(self):
        return self.name

    class Meta:
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
    source = models.FileField(
        verbose_name='Файл',
        upload_to='files/source/',
        storage=MinioBackend(bucket_name='local-media')
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Наименование'
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
        Concat(md5hash, sha256hash),
        editable=False,
        max_length=288,
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
    owner = models.ForeignKey(
        User,
        related_name='files',
        blank=True,
        null=True,
        verbose_name='Кто загрузил',
        on_delete=models.SET_NULL
    )
    file_type = models.PositiveSmallIntegerField(
        choices=TYPES,
        verbose_name='Тип'
    )
    tag = models.ManyToManyField(
        Tag,
        related_name='files',
        verbose_name='Тэг'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Файл'
        verbose_name_plural = 'Файлы'

    def __str__(self):
        return self.name

    @classmethod
    def create(cls, **kwargs):
        FILEINFO = GetFileInfo()
        custom_criteria = {
            'md5hash':    FILEINFO.get_md5(kwargs['source']),
            'sha256hash': FILEINFO.get_sha256(kwargs['source']),
            'length':     FILEINFO.get_length(kwargs['source']),
            'size':       FILEINFO.get_file_size(kwargs['source'])
        }
        obj = cls.objects.create(
            defaults=kwargs,
            **custom_criteria
        )
        return obj


class Playlist(models.Model):
    """Плейлисты."""

    name = models.CharField(
        max_length=255,
        verbose_name='Название'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Описание'
    )
    owner = models.ForeignKey(
        User,
        related_name='playlists',
        verbose_name='Создатель',
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    files = models.ManyToManyField(
        File,
        through='PlaylistFiles',
        related_name='playlist_files',
        verbose_name='Файлы'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Плейлист'
        verbose_name_plural = 'Плейлисты'

    def __str__(self):
        return self.name


class PlaylistFiles(models.Model):
    """Файл плейлиста."""

    playlist = models.ForeignKey(
        Playlist,
        related_name='playlist',
        verbose_name='Плейлист',
        on_delete=models.CASCADE
    )
    file = models.ForeignKey(
        File,
        related_name='file',
        verbose_name='Файл',
        on_delete=models.CASCADE
    )
    images = models.ManyToManyField(
        File,
        related_name='slides',
        verbose_name='Слайд'
    )

    class Meta:
        verbose_name = 'Файл плейлиста'
        verbose_name_plural = 'Файлы плейлиста'

    def __str__(self):
        return f'{self.file.name} - {self.playlist.name}'
