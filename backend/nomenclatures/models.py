import hashlib
from functools import lru_cache
from uuid import uuid4
from django.contrib.postgres.search import SearchVectorField

from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.validators import KeysValidator
from django.db import models
from django_minio_backend import MinioBackend
from django.utils.translation import gettext_lazy as _
from addresses.models import Address as AddressBook
from api import APIBaseObjectModel, Article, UUIDPKField
from django.utils import timezone

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

TYPES = {
    "interior": "Интерьер",
    "exterior": "Экстерьер"
}

AVAILABLE_CONTENT_TYPES = {
    "audio": "Аудио",
    "video": "Видео",
    "audio_video": "Аудио + Видео",
    "audio_video_image": "Аудио + Видео + Картинка",
    "video_image": "Видео + Картинка",
    "audio_image": "Аудио + Картинка",
}

STATUSES = {
    0: "Online",
    1: "Offline 5+ minutes",
    2: "Offline 1+ hour"
}


@lru_cache
def get_morph():
    import pymorphy3
    return pymorphy3.MorphAnalyzer()


def inflect_words(name: str, case: str):
    words = name.split()
    result = []
    morph = get_morph()

    for word in words:
        parsed = morph.parse(word)[0]
        inflected = parsed.inflect({case})

        if inflected:
            result.append(inflected.word)
        else:
            result.append(word)

    return " ".join(result)


class TypeOfPlace(models.Model):
    id = UUIDPKField()

    name = models.CharField(
        max_length=255,
        verbose_name="Полное наименование"
    )
    abbreviation = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Аббревиатура"
    )

    code1c = models.CharField(
        verbose_name="Код из 1С",
        max_length=64,
        blank=True,
        null=True,
        unique=True
    )

    genitive = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Название в родительном падеже"
    )

    prepositional = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Название в предложном падеже"
    )

    is_mall = models.BooleanField(
        default=False,
        verbose_name="Является торговым центром"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Активно"
    )

    class Meta:
        db_table = "type_of_place"
        verbose_name = "Тип места"
        verbose_name_plural = "Типы мест"

    @property
    def display_name(self):
        return self.abbreviation or self.name

    def save(self, *args, **kwargs):

        if not self.genitive and self.name:
            self.genitive = inflect_words(self.name, "gent")

        if not self.prepositional and self.name:
            self.prepositional = "в " + inflect_words(self.name, "loct")

        super().save(*args, **kwargs)


class MediaStorage(models.Model):
    class ContentType(models.TextChoices):
        AUDIO = "audio", "Аудио"
        VIDEO = "video", "Видео"

    id = UUIDPKField()
    name = models.CharField(
        verbose_name="Наименование",
        max_length=255
    )
    code1c = models.CharField(
        verbose_name="Код 1с",
        max_length=255,
        blank=True,
        null=True
    )

    content_type = models.CharField(
        max_length=50,
        choices=ContentType.choices,
        default=ContentType.AUDIO,
        blank=True
    )

    class Meta:
        db_table = "media_storage"
        constraints = [
            models.UniqueConstraint(
                fields=['code1c'],
                name="unique_media_storage_code1c"
            )
        ]
        indexes = [
            models.Index(fields=['code1c']),
            models.Index(fields=['name'])
        ]

class NomenclatureMediaStorage(models.Model):
    nomenclature = models.ForeignKey(
        'Nomenclature',
        on_delete=models.CASCADE
    )

    media = models.ForeignKey(
        MediaStorage,
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = "nomenclature_media_storage"
        unique_together = ('nomenclature', 'media')


class NomenclatureTenant(models.Model):
    nomenclature = models.ForeignKey(
        'Nomenclature',
        on_delete=models.CASCADE,
        related_name='nomenclature_tenants',
        verbose_name="Номенклатура"
    )
    tenant = models.ForeignKey(
        'counterparties.Counterparty',
        on_delete=models.CASCADE,
        related_name='tenant_nomenclatures',
        verbose_name="Арендатор"
    )
    floor = models.CharField(max_length=10, blank=True, verbose_name="Этаж")

    class Meta:
        db_table = "nomenclature_tenant"

        constraints = [
            models.UniqueConstraint(
                fields=['nomenclature', 'tenant'],
                name='unique_nomenclature_tenant'
            )
        ]

        indexes = [
            models.Index(fields=['nomenclature']),

            models.Index(fields=['tenant']),

            models.Index(fields=['tenant', 'nomenclature']),
        ]


class Nomenclature(APIBaseObjectModel):
    """Рабочая станция."""

    keys_validator = KeysValidator(
        keys=("mon", "tue", "wed", "thu", "fri", "sat", "sun"),
        strict=True
    )

    worktime_start = models.TimeField(
        auto_now_add=False,
        auto_now=False,
        verbose_name='Открытие'
    )

    worktime_end = models.TimeField(
        auto_now_add=False,
        auto_now=False,
        verbose_name="Закртыие"
    )

    id_rasb = models.CharField(
        null=True,
        blank=True,
        verbose_name="Id тачки",
        default=''
    )

    square = models.CharField(
        default="",
        null=True,
        blank=True,
        verbose_name="Площадь"
    )

    possibility = models.CharField(
        default="",
        null=True,
        blank=True,
        verbose_name="Проходимость"
    )

    media = models.ManyToManyField(
        'MediaStorage',
        through='NomenclatureMediaStorage',
        related_name="nomenclatures",
        verbose_name="Носители"
    )

    article = Article()

    description = models.TextField(
        blank=True, null=True, verbose_name="Описание"
    )
    search_vector = SearchVectorField(null=True, default='')
    search_vector_updated_at = models.DateTimeField(auto_now_add=True)

    responsible_radio = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="radio_nomenclature",
        verbose_name="Ответственный за радио"
    )

    responsible_ad = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ad_nomenclature",
        verbose_name="Ответственный за размещение"
    )

    responsible_technic = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="technic_nomenclature",
        verbose_name="Ответственный за технику"
    )

    responsible_technic_on_address = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="technic_on_address_nomenclature",
        verbose_name="Ответственный за технику на адресе"
    )

    responsible_placement_marketing = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="placement_marketing_nomenclature",
        verbose_name="Ответственный за маркетинг размещения"
    )

    timezone = models.CharField(
        choices=TIMEZONES,
        max_length=31,
        verbose_name="Часовой пояс",
        default="Etc/GMT-7",
    )

    code1c = models.CharField(
        verbose_name="Код из 1С",
        max_length=64,
        blank=True,
        null=True
    )

    version = models.CharField(
        max_length=127,
        verbose_name="Версия ПО"
    )

    settings = models.JSONField(
        verbose_name="Настройки вещания",
        validators=(keys_validator,),
        blank=True,
        default=dict
    )

    hw_info = models.JSONField(
        verbose_name="Информация о железе",
        blank=True, null=True
    )

    brand = models.ForeignKey(
        'brands.Brand',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Бренд номенклатуры",
        related_name="nomenclatures"
    )

    legalEntity = models.ForeignKey(
        'counterparties.Counterparty',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Юр. лицо",
        related_name="owned_nomenclatures"
    )

    tenants = models.ManyToManyField(
        'counterparties.Counterparty',
        through='NomenclatureTenant',
        related_name="rented_nomenclatures",
        verbose_name="Арендаторы"
    )

    contentType = models.CharField(
        max_length=255,
        choices=AVAILABLE_CONTENT_TYPES,
        default="audio",
    )

    typeOfPlace = models.ForeignKey(
        "TypeOfPlace",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="type_nomenclature",
        verbose_name="Тип места размещения"
    )

    pricePerMonth = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        verbose_name="Стоимость размещения в месяц",
        default=0.0,
    )

    @property
    def brand_logo(self):
        return self.brand.logotype

    @property
    def type_of_place_display(self):
        if not self.typeOfPlace:
            return None
        return self.typeOfPlace.abbreviation or self.typeOfPlace.name

    @property
    def name_for_front(self):

        if not self.brand:
            return None

        if not self.address or not self.address.address:
            return None

        if not self.address.address.city:
            return None

        if not self.address.address.house:
            return None

        brand = self.brand
        city = f"г. {self.address.address.city.name}"
        street = f"ул. {self.address.address.street.name}"
        house = self.address.address.house.number

        place = self.typeOfPlace

        if place:
            if place.abbreviation:
                place_name = place.abbreviation
            elif place.prepositional:
                place_name = place.prepositional
            else:
                place_name = place.name
        else:
            place_name = ""

        return f"Размещение ролика в {place_name} {brand.name}, {city}, {street}, {house}"

    def update_search_vector(self, tenants_text='', save=True):
        """Обновляет search_vector для конкретной номенклатуры"""
        from django.contrib.postgres.search import SearchVector
        from django.db.models import Value

        self.search_vector = (
                SearchVector(Value(self.name or ''), weight='A') +
                SearchVector(Value(self.contentType or ''), weight='C') +
                SearchVector(Value(self.typeOfPlace.name if self.typeOfPlace else ''), weight='B') +
                SearchVector(Value(self.version or ''), weight='B') +
                SearchVector(Value(self.code1c or ''), weight='A') +
                SearchVector(Value(self.brand.name if self.brand else ''), weight='A') +
                SearchVector(Value(self.legalEntity.first_name if self.legalEntity else ''), weight='A') +
                SearchVector(Value(self.legalEntity.last_name if self.legalEntity else ''), weight='B') +
                SearchVector(Value(self.legalEntity.keyword if self.legalEntity else ''), weight='A') +
                SearchVector(Value(self.legalEntity.additional_name if self.legalEntity else ''), weight='C') +
                SearchVector(Value(self.responsible_radio.first_name if self.responsible_radio else ''), weight='A') +
                SearchVector(Value(self.responsible_ad.first_name if self.responsible_ad else ''), weight='A') +
                SearchVector(Value(self.responsible_technic.first_name if self.responsible_technic else ''),
                             weight='A') +
                SearchVector(
                    Value(self.responsible_technic_on_address.last_name if self.responsible_technic_on_address else ''),
                    weight='B') +
                SearchVector(Value(self.responsible_radio.last_name if self.responsible_radio else ''), weight='B') +
                SearchVector(Value(self.responsible_ad.last_name if self.responsible_ad else ''), weight='B') +
                SearchVector(Value(self.responsible_technic.last_name if self.responsible_technic else ''),
                             weight='B') +
                SearchVector(Value(tenants_text), weight='B')
        )

        if save:
            self.search_vector_updated_at = timezone.now()
            self.save(update_fields=['search_vector', 'search_vector_updated_at'])

    def __str__(self):
        return self.name

    class Meta:
        db_table = "nomenclature"
        verbose_name = "Номенклатура"
        verbose_name_plural = "Номенклатуры"
        constraints = [
            models.UniqueConstraint(
                fields=["code1c"],
                name="unique_nomenclature_name",
                violation_error_message="Номенклатура с таким кодом уже существует",
            )
        ]
        indexes = [
            GinIndex(fields=['search_vector'], name='nomenclature_search_gin'),
            GinIndex(
                name='nomenclature_search_active_idx',
                fields=['search_vector'],
                condition=models.Q(is_active=True)  # Только для активных записей
            ),
            GinIndex(
                name="nomenclature_name_gin_idx",
                fields=["name"],
                opclasses=["gin_trgm_ops"],
            ),
            GinIndex(
                name="nomenclature_code1c_gin_idx",
                fields=["code1c"],
                opclasses=["gin_trgm_ops"],
            ),
            GinIndex(
                name="nomenclature_version_gin_idx",
                fields=["version"],
                opclasses=["gin_trgm_ops"],
            ),
            GinIndex(fields=['settings'], name='settings_gin_idx'),
            models.Index(fields=['typeOfPlace']),
            models.Index(fields=['responsible_radio']),
            models.Index(fields=['responsible_ad']),
            models.Index(
                fields=['brand'],
                name='idx_active_brand',
                condition=models.Q(is_active=True)
            ),
            models.Index(fields=['legalEntity']),

            # ДОБАВЛЯЕМ НЕДОСТАЮЩИЕ FK
            models.Index(fields=['responsible_technic']),
            models.Index(fields=['responsible_technic_on_address']),
            models.Index(fields=['responsible_placement_marketing']),

            # ИНДЕКСЫ ДЛЯ ПОИСКА ПО ТОЧНОМУ СОВПАДЕНИЮ
            models.Index(fields=['code1c']),
            models.Index(fields=['timezone']),
            models.Index(fields=['version']),

            # ИНДЕКС ДЛЯ СОРТИРОВКИ
            models.Index(fields=['pricePerMonth']),
            models.Index(fields=['-created']),

            # СОСТАВНЫЕ ИНДЕКСЫ ДЛЯ ЧАСТЫХ КОМБИНАЦИЙ
            models.Index(fields=['brand', 'typeOfPlace']),
            models.Index(fields=['legalEntity', 'brand']),

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
    nomenclature = models.OneToOneField(
        Nomenclature,
        verbose_name="Номенклатура",
        primary_key=True,
        on_delete=models.CASCADE,
        related_name="address",
    )
    address = models.ForeignKey(
        AddressBook,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Адрес из справочника",
    )

    class Meta:
        db_table = "nomenclature_addresses"
        verbose_name = "Адрес Номенклатуры"
        verbose_name_plural = "Ареса Номенклатур"


class StatusHistory(models.Model):
    """История изменения доступности."""

    client = models.ForeignKey(
        Nomenclature,
        verbose_name="Рабочая станция",
        related_name="history",
        on_delete=models.CASCADE,
    )
    change_time = models.DateTimeField(
        verbose_name="Время изменения статуса",
        auto_now_add=True
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

    class PhotoType(models.TextChoices):
        INTERIOR = "interior", _("Интерьер")
        EXTERIOR = "exterior", _("Экстерьер")
        SIGNAGE = "signage", _("Вывеска")
        INSTALLATION = "installation", _("Установка")

    id = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
        verbose_name="ИД"
    )

    source = models.FileField(
        verbose_name="Файл",
        upload_to=media_path,
        storage=MinioBackend(bucket_name="local-media"),
    )

    type = models.CharField(
        max_length=31,
        choices=PhotoType.choices,
        verbose_name="Тип фотографии"
    )

    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    nomenclature = models.ForeignKey(
        "Nomenclature",
        related_name="images",
        on_delete=models.CASCADE,
        verbose_name="Номенклатура",
    )

    hash = models.CharField(max_length=64, editable=False, db_index=True)

    def save(self, *args, **kwargs):
        if self.source:
            # читаем файл в бинарном режиме и считаем MD5
            file_data = self.source.read()
            self.hash = hashlib.md5(file_data).hexdigest()
            # возвращаем курсор файла в начало, иначе Django не сможет сохранить
            self.source.seek(0)
        super().save(*args, **kwargs)

    class Meta:
        db_table = "nomenclature_images"
        ordering = ("-created",)
        verbose_name = "Фотография номенклатуры"
        verbose_name_plural = "Фотографии номенклатур"

    def __str__(self):
        return f"{self.nomenclature} - {self.type}"
