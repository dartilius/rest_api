from uuid import uuid4

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.validators import KeysValidator
from django.db import models
from django_minio_backend import MinioBackend
from django.core.validators import RegexValidator
from api import APIBaseObjectModel, Article

TIMEZONES = {
    "Etc/GMT+11": "UTC -11",
    "Etc/GMT+10": "UTC -10",
    "Etc/GMT+9": "UTC -9",
    "Etc/GMT+8": "UTC -8",
    "Etc/GMT+7": "UTC -7",
    "Etc/GMT+6": "UTC -6",
    "Etc/GMT+5": "UTC -5",
    "Etc/GMT+4": "UTC -4",
    "Etc/GMT+3": "UTC -3",
    "Etc/GMT+2": "UTC -2",
    "Etc/GMT+1": "UTC -1",
    "Etc/GMT+0": "UTC",
    "Etc/GMT-1": "UTC +1",
    "Etc/GMT-2": "UTC +2",
    "Etc/GMT-3": "UTC +3",
    "Etc/GMT-4": "UTC +4",
    "Etc/GMT-5": "UTC +5",
    "Etc/GMT-6": "UTC +6",
    "Etc/GMT-7": "UTC +7",
    "Etc/GMT-8": "UTC +8",
    "Etc/GMT-9": "UTC +9",
    "Etc/GMT-10": "UTC +10",
    "Etc/GMT-11": "UTC +11",
    "Etc/GMT-12": "UTC +12",
}
TYPES = {"interior": "Интерьер", "exterior": "Экстерьер"}
AVAILABLE_CONTENT_TYPES = {
    "audio": "Аудио",
    "video": "Видео",
    "audio_video": "Аудио + Видео",
    "audio_video_image": "Аудио + Видео + Картинка",
    "video_image": "Видео + Картинка",
    "audio_image": "Аудио + Картинка",
}
STATUSES = {0: "Online", 1: "Offline 5+ minutes", 2: "Offline 1+ hour"}


class Brand(models.Model):
    """Бренд."""

    id = models.UUIDField(
        verbose_name="ИД", primary_key=True, editable=False, default=uuid4()
    )
    name = models.CharField(
        verbose_name="Наименование бренда", unique=True, max_length=255
    )
    logo = models.FileField(
        upload_to="brand_logo", storage=MinioBackend(bucket_name="local-media")
    )
    created = models.DateTimeField(
        verbose_name="Дата создания", auto_now_add=True
    )

    class Meta:
        db_table = "brands"
        verbose_name = "Бренд"
        verbose_name_plural = "Бренды"
        ordering = ("-created",)
        indexes = [
            GinIndex(
                name="brand_name_gin_idx",
                fields=["name"],
                opclasses=["gin_trgm_ops"],
            )
        ]


class Address(models.Model):
    """Адреса."""

    class Meta:
        abstract = True


class Nomenclature(APIBaseObjectModel):
    """Рабочая станция."""

    keys_validator = KeysValidator(
        keys=("mon", "tue", "wed", "thu", "fri", "sat", "sun"), strict=True
    )

    article = Article()
    description = models.TextField(
        blank=True, null=True, verbose_name="Описание"
    )
    timezone = models.CharField(
        choices=TIMEZONES,
        max_length=31,
        verbose_name="Часовой пояс",
        default="Etc/GMT-7",
    )
    version = models.CharField(max_length=127, verbose_name="Версия ПО")
    settings = models.JSONField(
        verbose_name="Настройки вещания", validators=(keys_validator,)
    )
    hw_info = models.JSONField(
        verbose_name="Информация о железе", blank=True, null=True
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Бренд номенклатуры",
    )
    legalEntity = models.CharField(max_length=255, null=True, blank=True)
    contentType = models.CharField(
        max_length=255,
        choices=AVAILABLE_CONTENT_TYPES,
        default="audio",
    )
    typeOfPlace = models.CharField(
        max_length=255,
        verbose_name="Тип места размещения",
        null=True,
        blank=True,
    )
    pricePerMonth = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        verbose_name="Стоимость размещения в месяц",
        default=0.0,
    )

    @property
    def brand_logo(self):
        return self.brand.logo

    def __str__(self):
        return self.name

    class Meta:
        db_table = "nomenclature"
        ordering = ("-created",)
        verbose_name = "Номенклатура"
        verbose_name_plural = "Номенклатуры"
        constraints = [
            models.UniqueConstraint(
                fields=["name"],
                name="unique_nomenclature_name",
                violation_error_message="Номенклатура с таким названием "
                "уже существует",
            )
        ]
        indexes = [
            GinIndex(
                name="nomenclature_name_gin_idx",
                fields=["name"],
                opclasses=["gin_trgm_ops"],
            )
        ]


class NomenclatureAvailability(models.Model):
    """Текущая доступность."""

    last_answer_date = models.DateTimeField(
        verbose_name="Время последнего ответа",
    )
    client = models.OneToOneField(
        Nomenclature,
        verbose_name="Рабочая станция",
        related_name="availability",
        on_delete=models.CASCADE,
    )
    status = models.PositiveSmallIntegerField(
        choices=STATUSES, verbose_name="Статус", default=2
    )

    class Meta:
        db_table = "availability"
        ordering = ("-last_answer_date",)
        verbose_name = "Время последнего ответа"
        verbose_name_plural = "Время последнего ответа"

    def __str__(self):
        return f"{self.last_answer_date}"


class NomenclatureAddress(models.Model):
    """Адреса номенклатур."""

    nomenclature = models.OneToOneField(
        Nomenclature,
        verbose_name="Номенклатура",
        primary_key=True,
        on_delete=models.CASCADE,
        related_name="address",
    )
    index = models.CharField(
        max_length=6,
        verbose_name="Почтовый индекс",
        validators=[RegexValidator(r'^\d{6}$', 'Индекс должен содержать 6 цифр')],
        null=True,
        blank=True
    )
    country = models.CharField(
        max_length=50,
        verbose_name="Страна",
        null=True,
        blank=True
    )
    city = models.CharField(
        max_length=50,
        verbose_name="Город",
        null=True,
        blank=True
    )
    locality = models.CharField(
        max_length=50,
        verbose_name="Тип населен. пункта",
        null=True,
        blank=True
    )
    region = models.CharField(
        max_length=50,
        verbose_name="Регион",
        null=True,
        blank=True
    )
    administrativeTerritory = models.CharField(
        max_length=50,
        verbose_name="Тип админ. терр. деления",
        null=True,
        blank=True
    )
    microdistrict = models.CharField(
        max_length=50,
        verbose_name="Микрорайон",
        null=True,
        blank=True
    )
    federalDistrict = models.CharField(
        max_length=50,
        verbose_name="Федеральный округ",
        null=True,
        blank=True
    )
    street = models.CharField(
        max_length=50,
        verbose_name="Улица",
        null=True,
        blank=True
    )
    street_house = models.CharField(
        max_length=31,
        verbose_name="Номер дома",
        null=True,
        blank=True
    )
    building = models.CharField(
        max_length=31,
        verbose_name="Строение",
        null=True,
        blank=True
    )
    coordinates = models.CharField(
        max_length=50,
        verbose_name="Координаты",
        null=True,
        blank=True
    )

    class Meta:
        db_table = "addresses"
        verbose_name = "Адрес номенклатуры"
        verbose_name_plural = "Адреса номенклатур"
        indexes = [
            models.Index(fields=['city']),
            models.Index(fields=['federalDistrict']),
            models.Index(fields=['street']),
            models.Index(fields=['city', 'street']),
        ]


class StatusHistory(models.Model):
    """История изменения доступности."""

    client = models.ForeignKey(
        Nomenclature,
        verbose_name="Рабочая станция",
        related_name="history",
        on_delete=models.CASCADE,
    )
    change_time = models.DateTimeField(
        verbose_name="Время изменения статуса", auto_now_add=True
    )
    status = models.PositiveSmallIntegerField(
        choices=STATUSES, verbose_name="Статус"
    )

    class Meta:
        db_table = "status_history"
        ordering = ("-change_time",)
        verbose_name = "История доступности"
        verbose_name_plural = "История доступности"

    def __str__(self):
        return (
            f"{self.change_time:%Y-%m-%d %H:%M:%S}: "
            f"статус {self.client.name} "
            f"изменился на {STATUSES[self.status][1]}"
        )


def media_path(instance, filename):
    return f"{TYPES[instance.type]}/{filename}"


class NomenclatureImage(models.Model):
    """Фотографии экстерьера и интерьера номенклатур."""

    id = models.UUIDField(
        verbose_name="ИД", editable=False, primary_key=True, default=uuid4()
    )
    source = models.FileField(
        verbose_name="Файл",
        upload_to=media_path,
        storage=MinioBackend(bucket_name="local-media"),
    )
    type = models.CharField(
        max_length=31, choices=TYPES, verbose_name="Тип фотографии"
    )
    created = models.DateTimeField(
        verbose_name="Дата создания", auto_now_add=True
    )
    nomenclature = models.ForeignKey(
        Nomenclature,
        related_name="images",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Номенклатура",
    )

    class Meta:
        db_table = "nomenclature_images"
        ordering = ("-created",)
        verbose_name = "Фотография номенклатуры"
        verbose_name_plural = "Фотографии номенклатур"
