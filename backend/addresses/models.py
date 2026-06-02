"""
Модели справочника адресов - иерархическая структура адресов.

В этом модуле определены все модели, необходимые для работы с иерархической системой адресов.
Система поддерживает многоуровневую структуру от стран до конкретных строений.

ИЕРАРХИЧЕСКАЯ СТРУКТУРА:
─────────────────────────────────────────────────────────────────────────────────────
1. Страна (Country)                          ──┐
2. Федеральный округ (FederalDistrict)      (только для России) ──┐
3. Тип региона (TypeRegion)                 (область, край, республика) ──┐
4. Регион (Region)                          (субъект федерации) ──┐
5. Часовой пояс (Timezone)                  (для регионов и городов) │
6. Тип населенного пункта (LocalityType)   (город, деревня, поселок) ──┐
7. Город (City)                            (населенный пункт) ──┐
8. Административный округ (AdministrativeTerritory) (для крупных городов) │
9. Административная единица (AdministrativeTerritorialUnit) (район/округ) │
10. Тип улицы (StreetType)                  (улица, проспект, переулок) ──┐
11. Улица (Street)                          ──┐
12. Дом (House)                             ──┐
13. Строение (Building)                     ──┐
14. Адрес (Address)                         (собирает всю иерархию)
─────────────────────────────────────────────────────────────────────────────────────

ОСОБЕННОСТИ СИСТЕМЫ:
• Все модели используют UUID в качестве первичного ключа
• Поддержка независимого создания элементов адреса
• Автоматическое заполнение пропущенных полей иерархии
• Гибкая система поиска и фильтрации
• Человекочитаемые форматы для часовых поясов
• Поддержка альтернативных названий для улучшения поиска
"""

import uuid
from django.core.validators import RegexValidator
from django.db import models
from django.contrib.postgres.indexes import GinIndex, BTreeIndex
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from django.core.exceptions import ValidationError
from transliterate import translit
import re

# ====================================================================================
# МОДУЛЬ 1: БАЗОВЫЕ МОДЕЛИ - СТРАНЫ И АДМИНИСТРАТИВНЫЕ ЕДИНИЦЫ
# ====================================================================================

class Country(models.Model):
    """
    МОДЕЛЬ СТРАНЫ - корневой элемент иерархии адресов.

    ОПИСАНИЕ:
    Представляет независимое государство. Является отправной точкой для всей
    иерархии адресов. Страна может иметь федеральные округа (для России) или
    напрямую содержать регионы (для других стран).

    АТРИБУТЫ:
    ──────────────────────────────────────────────────────────────────────────────
    id : UUIDField
        Уникальный идентификатор страны. Генерируется автоматически при создании.

    name : CharField
        Название страны. Обязательное поле, уникальное в рамках системы.
        Примеры: "Россия", "США", "Германия"
    ──────────────────────────────────────────────────────────────────────────────
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Уникальный идентификатор",
        help_text="Автоматически генерируемый UUID идентификатор страны"
    )

    name = models.CharField(
        "Название страны",
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Полное официальное название страны на русском языке"
    )

    class Meta:
        verbose_name = "Страна"
        verbose_name_plural = "Страны"
        db_table = "addresses_country"
        ordering = ['name']

        indexes = [
            BTreeIndex(fields=['name'], name='country_name_btree_idx'),
            GinIndex(
                fields=['name'],
                name='country_name_gin_idx',
                opclasses=['gin_trgm_ops']
            ),
        ]

    def __str__(self):
        """Строковое представление страны."""
        return self.name

    def clean(self):
        """Валидация данных страны перед сохранением."""
        from django.core.exceptions import ValidationError

        if not self.name or self.name.strip() == '':
            raise ValidationError({'name': 'Название страны не может быть пустым'})

        if len(self.name) > 255:
            raise ValidationError({'name': 'Название страны слишком длинное (максимум 255 символов)'})

    def save(self, *args, **kwargs):
        """Сохранение модели страны с дополнительной обработкой."""
        self.full_clean()
        super().save(*args, **kwargs)


class FederalDistrict(models.Model):
    """
    МОДЕЛЬ ФЕДЕРАЛЬНОГО ОКРУГА - административная единица высшего уровня.

    ОПИСАНИЕ:
    Представляет федеральный округ в странах с федеративным устройством
    (в основном в России). Каждый федеральный округ принадлежит одной стране
    и содержит несколько регионов.

    АТРИБУТЫ:
    ──────────────────────────────────────────────────────────────────────────────
    id : UUIDField
        Уникальный идентификатор федерального округа

    country : ForeignKey → Country
        Страна, к которой относится федеральный округ

    name : CharField
        Название федерального округа
        Примеры: "Центральный федеральный округ", "Северо-Западный федеральный округ"

    abbreviated_name : CharField
        Сокращенное название федерального округа
        Примеры: "ЦФО", "СЗФО", "ЮФО"
    ──────────────────────────────────────────────────────────────────────────────
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Уникальный идентификатор"
    )

    country = models.ForeignKey(
        'Country',
        on_delete=models.PROTECT,
        related_name="federal_districts",
        verbose_name="Страна",
        help_text="Страна, к которой относится федеральный округ"
    )

    name = models.CharField(
        "Название федерального округа",
        max_length=255,
        help_text="Полное название федерального округа"
    )

    abbreviated_name = models.CharField(
        "Сокращенное название",
        max_length=50,
        help_text="Сокращенное название (например, ЦФО, СЗФО, ЮФО)"
    )

    class Meta:
        verbose_name = "Федеральный округ"
        verbose_name_plural = "Федеральные округа"
        db_table = "addresses_federal_district"
        ordering = ['country__name', 'name']
        unique_together = ['country', 'name']

        indexes = [
            BTreeIndex(fields=['name'], name='federal_district_name_idx'),
            BTreeIndex(fields=['country', 'name'], name='federal_distr_country_name_idx'),
            GinIndex(
                fields=['name'],
                name='federal_district_name_gin_idx',
                opclasses=['gin_trgm_ops']
            ),
        ]

    def __str__(self):
        """Строковое представление федерального округа."""
        return f"{self.name} ({self.country.name})"


class TypeRegion(models.Model):
    """
    МОДЕЛЬ ТИПА РЕГИОНА - классификация регионов по административному статусу.

    ОПИСАНИЕ:
    Определяет тип региона (область, край, республика, город федерального значения)
    и правила отображения этого типа в полном названии региона.

    АТРИБУТЫ:
    ──────────────────────────────────────────────────────────────────────────────
    name : CharField
        Полное название типа региона
        Примеры: "область", "край", "республика", "город федерального значения"

    abbreviated_name : CharField
        Сокращенное название типа
        Примеры: "обл.", "кр.", "респ.", "г.ф.з."

    show_before_name : BooleanField
        Определяет позицию типа относительно названия региона
        True: "Область Московская"
        False: "Московская область" (по умолчанию)

    skip_in_name : BooleanField
        Флаг, указывающий пропускать ли тип при формировании полного названия
        True: "Москва" (без "г. Москва")
        False: "г. Москва" (по умолчанию)
    ──────────────────────────────────────────────────────────────────────────────
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Уникальный идентификатор"
    )

    name = models.CharField(
        "Тип региона",
        max_length=255,
        unique=True,
        help_text="Полное название типа региона (область, край, республика и т.д.)"
    )

    abbreviated_name = models.CharField(
        "Сокращенное название",
        max_length=50,
        help_text="Сокращенное название типа (обл., кр., респ. и т.д.)"
    )

    show_before_name = models.BooleanField(
        "Тип перед названием",
        default=False,
        help_text="Если отмечено: 'Область Московская', если нет: 'Московская область'"
    )

    skip_in_name = models.BooleanField(
        "Пропускать тип в названии",
        default=False,
        help_text="Не отображать тип региона при выводе полного названия"
    )

    class Meta:
        verbose_name = "Тип региона"
        verbose_name_plural = "Типы регионов"
        db_table = "addresses_type_region"
        ordering = ['name']

        indexes = [
            BTreeIndex(fields=['name'], name='type_region_name_idx'),
            GinIndex(
                fields=['name'],
                name='type_region_name_gin_idx',
                opclasses=['gin_trgm_ops']
            ),
        ]

    def __str__(self):
        """Строковое представление типа региона."""
        return self.name


class Timezone(models.Model):
    """
    МОДЕЛЬ ЧАСОВОГО ПОЯСА - временные зоны для регионов и городов.

    ОПИСАНИЕ:
    Хранит информацию о часовых поясах, включая смещение относительно UTC
    и московского времени. Используется для правильного отображения времени
    в различных регионах.

    АТРИБУТЫ:
    ──────────────────────────────────────────────────────────────────────────────
    id : UUIDField
        Уникальный идентификатор часового пояса

    name : CharField
        Наименование часового пояса
        Примеры: "Московское время", "Екатеринбургское время"

    offset_utc : IntegerField
        Смещение относительно UTC в часах
        Примеры: +3, +5, -2

    offset_moscow : IntegerField
        Смещение относительно московского времени в часах
        Примеры: 0, +2, -1
    ──────────────────────────────────────────────────────────────────────────────
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Уникальный идентификатор"
    )

    name = models.CharField(
        "Наименование часового пояса",
        max_length=255,
        unique=True,
        help_text="Название часового пояса (например, Московское время)"
    )

    offset_utc = models.IntegerField(
        "Смещение относительно UTC",
        help_text="Смещение относительно времени по Гринвичу в часах (например: +3, +5, -2)"
    )

    offset_moscow = models.IntegerField(
        "Смещение относительно Москвы",
        help_text="Смещение относительно московского времени в часах (например: 0, +2, -1)"
    )

    class Meta:
        verbose_name = "Часовой пояс"
        verbose_name_plural = "Часовые пояса"
        db_table = "addresses_timezone"
        ordering = ['offset_utc']

        indexes = [
            BTreeIndex(fields=['offset_utc'], name='timezone_offset_idx'),
            GinIndex(
                fields=['name'],
                name='timezone_name_gin_idx',
                opclasses=['gin_trgm_ops']
            ),
        ]

    def __str__(self):
        """Форматированное строковое представление часового пояса."""
        utc_sign = '+' if self.offset_utc >= 0 else ''
        msk_sign = '+' if self.offset_moscow >= 0 else ''
        return f"{self.name} (UTC{utc_sign}{self.offset_utc}, МСК{msk_sign}{self.offset_moscow})"


class Region(models.Model):
    """
    МОДЕЛЬ РЕГИОНА - субъект федерации или административная единица страны.

    ОПИСАНИЕ:
    Представляет регион (субъект федерации) в составе страны. Регион может
    иметь тип (область, край, республика) и принадлежать федеральному округу.
    Содержит информацию о часовом поясе.

    АТРИБУТЫ:
    ──────────────────────────────────────────────────────────────────────────────
    id : UUIDField
        Уникальный идентификатор региона

    name : CharField
        Наименование региона
        Примеры: "Московская", "Ленинградская", "Татарстан"

    abbreviated_name : CharField
        Сокращенное наименование региона
        Примеры: "МО", "ЛО", "РТ"

    federal_district : ForeignKey → FederalDistrict
        Федеральный округ, к которому относится регион

    type_region : ForeignKey → TypeRegion
        Тип региона (область, край, республика и т.д.)

    timezone : ForeignKey → Timezone
        Часовой пояс региона (необязательно)
    ──────────────────────────────────────────────────────────────────────────────
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Уникальный идентификатор"
    )

    name = models.CharField(
        "Наименование региона",
        max_length=255,
        help_text="Название региона без указания типа"
    )

    abbreviated_name = models.CharField(
        "Сокращенное наименование",
        max_length=255,
        blank=True,
        null=True,
        help_text="Сокращенное название региона (если есть)"
    )

    federal_district = models.ForeignKey(
        "FederalDistrict",
        on_delete=models.PROTECT,
        related_name="regions",
        verbose_name="Федеральный округ",
        help_text="Федеральный округ, в который входит регион"
    )

    type_region = models.ForeignKey(
        "TypeRegion",
        on_delete=models.PROTECT,
        related_name="regions",
        verbose_name="Тип региона",
        help_text="Тип региона (область, край, республика и т.д.)"
    )

    timezone = models.ForeignKey(
        "Timezone",
        on_delete=models.PROTECT,
        related_name="regions",
        verbose_name="Часовой пояс",
        null=True,
        blank=True,
        help_text="Часовой пояс региона (если отличается от стандартного)"
    )

    class Meta:
        verbose_name = "Регион"
        verbose_name_plural = "Регионы"
        db_table = "addresses_region"
        unique_together = ("federal_district", "name")
        ordering = ['federal_district__name', 'name']

        indexes = [
            BTreeIndex(fields=['name'], name='region_name_idx'),
            BTreeIndex(fields=['federal_district', 'name'], name='region_fd_name_idx'),
            GinIndex(
                fields=['name'],
                name='region_name_gin_idx',
                opclasses=['gin_trgm_ops']
            ),
        ]

    def __str__(self):
        """
        ФОРМАТИРОВАННОЕ СТРОКОВОЕ ПРЕДСТАВЛЕНИЕ РЕГИОНА.
        
        ОПТИМИЗИРОВАННАЯ ВЕРСИЯ:
        • Проверяет наличие загруженного type_region
        • Использует кэширование через hasattr
        • Не вызывает дополнительных запросов при предзагрузке
        """
        # Проверяем, загружен ли type_region (через select_related)
        if hasattr(self, '_cached_type_region'):
            type_region = self._cached_type_region
        else:
            type_region = self.type_region
        
        if type_region and not type_region.skip_in_name:
            if type_region.show_before_name:
                return f"{type_region.abbreviated_name} {self.name}"
            else:
                return f"{self.name} {type_region.abbreviated_name}"
        return self.name

    # def __str__(self):
    #     """Форматированное строковое представление региона."""
    #     if self.type_region and not self.type_region.skip_in_name:
    #         if self.type_region.show_before_name:
    #             return f"{self.type_region.abbreviated_name} {self.name}"
    #         else:
    #             return f"{self.name} {self.type_region.abbreviated_name}"
    #     return self.name


# ====================================================================================
# МОДУЛЬ 2: НАСЕЛЕННЫЕ ПУНКТЫ И АДМИНИСТРАТИВНЫЕ ЕДИНИЦЫ
# ====================================================================================

class LocalityType(models.Model):
    """
    МОДЕЛЬ ТИПА НАСЕЛЕННОГО ПУНКТА - классификация населенных пунктов.

    ОПИСАНИЕ:
    Определяет тип населенного пункта (город, деревня, поселок и т.д.)
    и правила его отображения. Также указывает, имеет ли данный тип
    административные округа (для городов федерального значения).

    АТРИБУТЫ:
    ──────────────────────────────────────────────────────────────────────────────
    id : UUIDField
        Уникальный идентификатор типа населенного пункта

    name : CharField
        Тип населенного пункта
        Примеры: "город", "деревня", "поселок", "село"

    abbreviated_name : CharField
        Сокращенное наименование типа
        Примеры: "г.", "д.", "п.", "с."

    show_before_name : BooleanField
        Определяет позицию типа относительно названия
        True: "г. Москва"
        False: "Москва г." (по умолчанию)

    has_administrative_territory : BooleanField
        Имеет ли данный тип административные округа
        True: для городов федерального значения
        False: для обычных населенных пунктов
    ──────────────────────────────────────────────────────────────────────────────
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Уникальный идентификатор"
    )

    name = models.CharField(
        "Тип населённого пункта",
        max_length=255,
        unique=True,
        help_text="Тип населенного пункта (город, деревня, поселок и т.д.)"
    )

    abbreviated_name = models.CharField(
        "Сокращённое наименование",
        max_length=50,
        blank=True,
        null=True,
        help_text="Сокращенное обозначение типа (г., д., п. и т.д.)"
    )

    show_before_name = models.BooleanField(
        "Отображать тип до наименования",
        default=False,
        help_text="Если отмечено: 'г. Москва', если нет: 'Москва г.'"
    )

    has_administrative_territory = models.BooleanField(
        "Имеет административный округ",
        default=False,
        help_text="Для городов федерального значения (Москва, Санкт-Петербург)"
    )

    class Meta:
        verbose_name = "Тип населённого пункта"
        verbose_name_plural = "Типы населённых пунктов"
        db_table = "addresses_locality_type"
        ordering = ['name']

        indexes = [
            BTreeIndex(fields=['name'], name='locality_type_name_idx'),
            GinIndex(
                fields=['name'],
                name='locality_type_name_gin_idx',
                opclasses=['gin_trgm_ops']
            ),
        ]

    def __str__(self):
        """Строковое представление типа населенного пункта."""
        return self.name


class City(models.Model):
    """
    МОДЕЛЬ ГОРОДА / НАСЕЛЕННОГО ПУНКТА - основной элемент адресной системы.

    ОПИСАНИЕ:
    Представляет населенный пункт (город, деревню, поселок и т.д.).
    Содержит информацию о регионе, типе населенного пункта, часовом поясе
    и административной структуре.

    АТРИБУТЫ:
    ──────────────────────────────────────────────────────────────────────────────
    id : UUIDField
        Уникальный идентификатор города

    name : CharField
        Наименование города
        Примеры: "Москва", "Санкт-Петербург", "Новосибирск"

    region : ForeignKey → Region
        Регион, к которому относится город

    locality_type : ForeignKey → LocalityType
        Тип населенного пункта

    timezone : ForeignKey → Timezone
        Часовой пояс города (необязательно)

    has_atd : BooleanField
        Наличие административно-территориального деления

    atd_type : CharField
        Тип административно-территориального деления

    has_administrative_territory : BooleanField
        Наличие административного округа
    ──────────────────────────────────────────────────────────────────────────────
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Уникальный идентификатор"
    )

    name = models.CharField(
        "Наименование города",
        max_length=255,
        help_text="Название населенного пункта"
    )

    slug = models.SlugField(
        "Наименование города - транслит",
        max_length=255,
        help_text="Название населенного пункта (АВТО)"
    )

    region = models.ForeignKey(
        "Region",
        on_delete=models.PROTECT,
        related_name="cities",
        verbose_name="Регион",
        help_text="Регион, к которому относится город"
    )

    locality_type = models.ForeignKey(
        "LocalityType",
        on_delete=models.PROTECT,
        related_name="cities",
        verbose_name="Тип населённого пункта",
        help_text="Тип населенного пункта (город, деревня и т.д.)"
    )

    timezone = models.ForeignKey(
        "Timezone",
        on_delete=models.PROTECT,
        related_name="cities",
        verbose_name="Часовой пояс",
        null=True,
        blank=True,
        help_text="Часовой пояс города (если отличается от регионального)"
    )

    has_atd = models.BooleanField(
        "Наличие АТД",
        default=False,
        help_text="Наличие административно-территориального деления"
    )

    atd_type = models.CharField(
        "Тип АТД",
        max_length=255,
        blank=True,
        null=True,
        help_text="Тип административно-территориального деления"
    )

    has_administrative_territory = models.BooleanField(
        "Наличие административного округа",
        default=False,
        help_text="Наличие административных округов (например, в Москве)"
    )

    class Meta:
        verbose_name = "Населённый пункт"
        verbose_name_plural = "Населённые пункты"
        db_table = "addresses_city"
        unique_together = ("region", "name")
        ordering = ['region__name', 'name']

        indexes = [
            BTreeIndex(fields=['name'], name='city_name_idx'),
            BTreeIndex(fields=['region', 'name'], name='city_region_name_idx'),
            GinIndex(
                fields=['name'],
                name='city_name_gin_idx',
                opclasses=['gin_trgm_ops']
            ),
        ]

    def save(self, *args, **kwargs):
        self.slug = self._generate_slug()
        super().save(*args, **kwargs)

    def _generate_slug(self):
        try:
            name_latin = translit(self.name, 'ru', reversed=True)
        except Exception:
            name_latin = self.name

        base = re.sub(r'[^\w\s-]', '', name_latin.lower()).strip()
        base = re.sub(r'[\s_-]+', '-', base) or str(self.id)[:8]
        slug = base[:90]

        if City.objects.filter(slug=slug).exclude(id=self.id).exists():
            slug = f"{slug[:85]}-{str(self.id)[:8]}"

        return slug

    def __str__(self):
        """
        ФОРМАТИРОВАННОЕ СТРОКОВОЕ ПРЕДСТАВЛЕНИЕ ГОРОДА.
        
        ОПТИМИЗИРОВАННАЯ ВЕРСИЯ:
        • Проверяет наличие загруженного locality_type
        • Использует кэширование через hasattr
        """
        # Проверяем, загружен ли locality_type
        if hasattr(self, '_cached_locality_type'):
            locality_type = self._cached_locality_type
        else:
            locality_type = self.locality_type
        
        if locality_type:
            if locality_type.show_before_name:
                prefix = locality_type.abbreviated_name or locality_type.name
                return f"{prefix} {self.name}"
            else:
                suffix = locality_type.abbreviated_name or locality_type.name
                return f"{self.name} {suffix}"
        return self.name

    # def __str__(self):
    #     """Форматированное строковое представление города."""
    #     if self.locality_type:
    #         if self.locality_type.show_before_name:
    #             prefix = self.locality_type.abbreviated_name or self.locality_type.name
    #             return f"{prefix} {self.name}"
    #         else:
    #             suffix = self.locality_type.abbreviated_name or self.locality_type.name
    #             return f"{self.name} {suffix}"
    #     return self.name


class AdministrativeTerritory(models.Model):
    """
    МОДЕЛЬ АДМИНИСТРАТИВНОГО ОКРУГА - для крупных городов с делением.

    ОПИСАНИЕ:
    Представляет административный округ в крупных городах (например,
    административные округа Москвы). Создается только для городов,
    у которых LocalityType.has_administrative_territory = True.

    АТРИБУТЫ:
    ──────────────────────────────────────────────────────────────────────────────
    id : UUIDField
        Уникальный идентификатор административного округа

    city : ForeignKey → City
        Город, к которому относится округ

    name : CharField
        Название административного округа
        Примеры: "Центральный административный округ", "Северный административный округ"
    ──────────────────────────────────────────────────────────────────────────────
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Уникальный идентификатор"
    )

    city = models.ForeignKey(
        "City",
        on_delete=models.PROTECT,
        related_name="administrative_territories",
        verbose_name="Город",
        help_text="Город, в котором находится административный округ"
    )

    name = models.CharField(
        "Административный округ",
        max_length=255,
        help_text="Название административного округа"
    )

    class Meta:
        verbose_name = "Административный округ"
        verbose_name_plural = "Административные округа"
        db_table = "addresses_administrative_territory"
        unique_together = ("city", "name")
        ordering = ['city__name', 'name']

        indexes = [
            BTreeIndex(fields=['name'], name='admin_territory_name_idx'),
            BTreeIndex(fields=['city', 'name'], name='admin_territory_city_name_idx'),
            GinIndex(
                fields=['name'],
                name='admin_territory_name_gin_idx',
                opclasses=['gin_trgm_ops']
            ),
        ]

    def __str__(self):
        """Строковое представление административного округа."""
        return f"{self.name} ({self.city.name})"


class AdministrativeTerritorialUnit(models.Model):
    """
    МОДЕЛЬ АДМИНИСТРАТИВНО-ТЕРРИТОРИАЛЬНОЙ ЕДИНИЦЫ - район или округ в городе.

    ОПИСАНИЕ:
    Представляет район или округ в пределах города или административного округа.
    Например, районы Москвы или муниципальные округи.

    АТРИБУТЫ:
    ──────────────────────────────────────────────────────────────────────────────
    id : UUIDField
        Уникальный идентификатор АТЕ

    name : CharField
        Название района/округа
        Примеры: "Арбат", "Хамовники", "Василеостровский район"

    city : ForeignKey → City
        Город, к которому относится АТЕ

    administrative_territory : ForeignKey → AdministrativeTerritory
        Административный округ (необязательно)
    ──────────────────────────────────────────────────────────────────────────────
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Уникальный идентификатор"
    )

    name = models.CharField(
        "Район / округ",
        max_length=255,
        help_text="Название административно-территориальной единицы"
    )

    city = models.ForeignKey(
        "City",
        on_delete=models.PROTECT,
        related_name="territorial_units",
        verbose_name="Город",
        help_text="Город, в котором находится район/округ"
    )

    administrative_territory = models.ForeignKey(
        "AdministrativeTerritory",
        on_delete=models.PROTECT,
        related_name="territorial_units",
        verbose_name="Административный округ",
        null=True,
        blank=True,
        help_text="Административный округ (если район входит в округ)"
    )

    class Meta:
        verbose_name = "Административно-территориальная единица"
        verbose_name_plural = "Административно-территориальные единицы"
        db_table = "addresses_administrative_territorial_unit"
        unique_together = ("city", "name")
        ordering = ['city__name', 'name']

        indexes = [
            BTreeIndex(fields=['name'], name='admin_unit_name_idx'),
            BTreeIndex(fields=['city', 'name'], name='admin_unit_city_name_idx'),
            GinIndex(
                fields=['name'],
                name='admin_unit_name_gin_idx',
                opclasses=['gin_trgm_ops']
            ),
        ]

    def __str__(self):
        """Строковое представление административно-территориальной единицы."""
        if self.administrative_territory:
            return f"{self.name} ({self.administrative_territory.name})"
        return f"{self.name} ({self.city.name})"


# ====================================================================================
# МОДУЛЬ 3: УЛИЧНО-ДОМОВАЯ СЕТЬ
# ====================================================================================

class StreetType(models.Model):
    """
    МОДЕЛЬ ТИПА УЛИЦЫ - классификация улиц по типу.

    ОПИСАНИЕ:
    Определяет тип улицы (улица, проспект, переулок и т.д.)
    и правила его отображения в адресе.

    АТРИБУТЫ:
    ──────────────────────────────────────────────────────────────────────────────
    id : UUIDField
        Уникальный идентификатор типа улицы

    name : CharField
        Тип улицы
        Примеры: "улица", "проспект", "переулок", "бульвар"

    abbreviated_name : CharField
        Сокращенное наименование типа
        Примеры: "ул.", "пр.", "пер.", "б-р"

    show_before_name : BooleanField
        Определяет позицию типа относительно названия улицы
        True: "ул. Ленина"
        False: "Ленина ул." (по умолчанию True)
    ──────────────────────────────────────────────────────────────────────────────
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Уникальный идентификатор"
    )

    name = models.CharField(
        "Тип улицы",
        max_length=255,
        unique=True,
        help_text="Тип улицы (улица, проспект, переулок и т.д.)"
    )

    abbreviated_name = models.CharField(
        "Сокращённое наименование",
        max_length=50,
        blank=True,
        null=True,
        help_text="Сокращенное обозначение типа (ул., пр., пер. и т.д.)"
    )

    show_before_name = models.BooleanField(
        "Отображать тип до наименования",
        default=True,
        help_text="Если отмечено: 'ул. Ленина', если нет: 'Ленина ул.'"
    )

    class Meta:
        verbose_name = "Тип улицы"
        verbose_name_plural = "Типы улиц"
        db_table = "addresses_street_type"
        ordering = ['name']

        indexes = [
            BTreeIndex(fields=['name'], name='street_type_name_idx'),
            GinIndex(
                fields=['name'],
                name='street_type_name_gin_idx',
                opclasses=['gin_trgm_ops']
            ),
        ]

    def __str__(self):
        """Строковое представление типа улицы."""
        return self.name


class Street(models.Model):
    """
    МОДЕЛЬ УЛИЦЫ - элемент адресной системы между городом и домом.

    ОПИСАНИЕ:
    Представляет улицу, проспект, переулок и т.д. в пределах города.
    Содержит информацию о городе и типе улицы.

    АТРИБУТЫ:
    ──────────────────────────────────────────────────────────────────────────────
    id : UUIDField
        Уникальный идентификатор улицы

    city : ForeignKey → City
        Город, к которому относится улица

    street_type : ForeignKey → StreetType
        Тип улицы (необязательно)

    name : CharField
        Наименование улицы
        Примеры: "Ленина", "Победы", "Центральная"
    ──────────────────────────────────────────────────────────────────────────────
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Уникальный идентификатор"
    )

    city = models.ForeignKey(
        "City",
        on_delete=models.PROTECT,
        related_name="streets",
        verbose_name="Город",
        help_text="Город, в котором находится улица"
    )

    street_type = models.ForeignKey(
        "StreetType",
        on_delete=models.PROTECT,
        related_name="streets",
        verbose_name="Тип улицы",
        null=True,
        blank=True,
        help_text="Тип улицы (если известен)"
    )

    name = models.CharField(
        "Наименование улицы",
        max_length=255,
        help_text="Название улицы без указания типа"
    )

    class Meta:
        verbose_name = "Улица"
        verbose_name_plural = "Улицы"
        db_table = "addresses_street"
        unique_together = ("city", "name")
        ordering = ['city__name', 'name']

        indexes = [
            BTreeIndex(fields=['name'], name='street_name_idx'),
            BTreeIndex(fields=['city', 'name'], name='street_city_name_idx'),
            GinIndex(
                fields=['name'],
                name='street_name_gin_idx',
                opclasses=['gin_trgm_ops']
            ),
        ]

    def __str__(self):
        """
        ФОРМАТИРОВАННОЕ СТРОКОВОЕ ПРЕДСТАВЛЕНИЕ УЛИЦЫ.
        
        ОПТИМИЗИРОВАННАЯ ВЕРСИЯ:
        • Проверяет наличие загруженного street_type
        """
        if hasattr(self, '_cached_street_type'):
            street_type = self._cached_street_type
        else:
            street_type = self.street_type
        
        if street_type:
            if street_type.show_before_name:
                prefix = street_type.abbreviated_name or street_type.name
                return f"{prefix} {self.name}"
            else:
                suffix = street_type.abbreviated_name or street_type.name
                return f"{self.name} {suffix}"
        return self.name

    # def __str__(self):
    #     """Форматированное строковое представление улицы."""
    #     if self.street_type:
    #         if self.street_type.show_before_name:
    #             prefix = self.street_type.abbreviated_name or self.street_type.name
    #             return f"{prefix} {self.name}"
    #         else:
    #             suffix = self.street_type.abbreviated_name or self.street_type.name
    #             return f"{self.name} {suffix}"
    #     return self.name


class House(models.Model):
    """
    МОДЕЛЬ ДОМА - здание на улице с номером.

    ОПИСАНИЕ:
    Представляет дом (здание) на улице. Содержит номер дома и ссылку на улицу.

    АТРИБУТЫ:
    ──────────────────────────────────────────────────────────────────────────────
    id : UUIDField
        Уникальный идентификатор дома

    street : ForeignKey → Street
        Улица, на которой расположен дом

    number : CharField
        Номер дома
        Примеры: "1", "12А", "24/2", "15к1"
    ──────────────────────────────────────────────────────────────────────────────
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Уникальный идентификатор"
    )

    street = models.ForeignKey(
        "Street",
        on_delete=models.PROTECT,
        related_name="houses",
        verbose_name="Улица",
        help_text="Улица, на которой расположен дом"
    )

    number = models.CharField(
        "Номер дома",
        max_length=31,
        help_text="Номер дома (может содержать буквы и дроби)"
    )

    class Meta:
        verbose_name = "Дом"
        verbose_name_plural = "Дома"
        db_table = "addresses_house"
        unique_together = ("street", "number")
        ordering = ['street__name', 'number']

        indexes = [
            BTreeIndex(fields=['number'], name='house_number_idx'),
            BTreeIndex(fields=['street', 'number'], name='house_street_number_idx'),
            GinIndex(
                fields=['number'],
                name='house_number_gin_idx',
                opclasses=['gin_trgm_ops']
            ),
        ]

    def __str__(self):
        """Строковое представление дома."""
        return f"{self.street}, д. {self.number}"


class Building(models.Model):
    """
    МОДЕЛЬ СТРОЕНИЯ / КОРПУСА - дополнительные строения на участке дома.

    ОПИСАНИЕ:
    Представляет строение или корпус на участке дома. Используется для
    адресов, где есть несколько зданий под одним номером дома.

    АТРИБУТЫ:
    ──────────────────────────────────────────────────────────────────────────────
    id : UUIDField
        Уникальный идентификатор строения

    house : ForeignKey → House
        Дом, к которому относится строение

    number : CharField
        Номер строения/корпуса
        Примеры: "1", "А", "Б", "строение 1"
    ──────────────────────────────────────────────────────────────────────────────
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Уникальный идентификатор"
    )

    house = models.ForeignKey(
        "House",
        on_delete=models.PROTECT,
        related_name="buildings",
        verbose_name="Дом",
        help_text="Дом, к которому относится строение"
    )

    number = models.CharField(
        "Корпус / строение",
        max_length=31,
        help_text="Номер корпуса или строения"
    )

    class Meta:
        verbose_name = "Здание / строение"
        verbose_name_plural = "Здания / строения"
        db_table = "addresses_building"
        unique_together = ("house", "number")
        ordering = ['house__street__name', 'house__number', 'number']

        indexes = [
            BTreeIndex(fields=['number'], name='building_number_idx'),
            BTreeIndex(fields=['house', 'number'], name='building_house_number_idx'),
            GinIndex(
                fields=['number'],
                name='building_number_gin_idx',
                opclasses=['gin_trgm_ops']
            ),
        ]

    def __str__(self):
        """Строковое представление строения."""
        return f"{self.house}, стр. {self.number}"

class Coordinates(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Уникальный идентификатор"
    )

    latitude = models.CharField(
        verbose_name="Широта",
        max_length=31,
        blank=True,
        null=True,
        help_text="Географическая широта в градусах (от -90 до 90)"
    )

    longitude = models.CharField(
        verbose_name="Долгота",
        max_length=31,
        blank=True,
        null=True,
        help_text="Географическая долгота в градусах (от -180 до 180)"
    )

    class Meta:
        verbose_name = "Координаты"
        verbose_name_plural = "Координаты"
        db_table = "addresses_coordinates"
# ====================================================================================
# МОДУЛЬ 4: ПОЛНЫЙ АДРЕС И ФИНАЛЬНЫЕ МОДЕЛИ
# ====================================================================================

class Address(models.Model):
    """
    МОДЕЛЬ АДРЕСА - собирает всю иерархию в один объект.

    ОПИСАНИЕ:
    Финальная модель, которая объединяет все элементы адресной иерархии
    в один объект. Позволяет хранить полный адрес с возможностью получения
    отдельных компонентов. Поддерживает дополнительные поля: микрорайон,
    почтовый индекс, координаты.

    АТРИБУТЫ:
    ──────────────────────────────────────────────────────────────────────────────
    id : UUIDField
        Уникальный идентификатор адреса

    country : ForeignKey → Country
        Страна (необязательно, может быть выведена из иерархии)

    federal_district : ForeignKey → FederalDistrict
        Федеральный округ (необязательно)

    region : ForeignKey → Region
        Регион (необязательно)

    city : ForeignKey → City
        Город (необязательно)

    administrative_territory : ForeignKey → AdministrativeTerritory
        Административный округ (необязательно)

    administrative_unit : ForeignKey → AdministrativeTerritorialUnit
        Административно-территориальная единица (необязательно)

    street : ForeignKey → Street
        Улица (необязательно)

    house : ForeignKey → House
        Дом (необязательно)

    building : ForeignKey → Building
        Строение (необязательно)

    microdistrict : CharField
        Микрорайон (необязательно)

    index : CharField
        Почтовый индекс (6 цифр, необязательно)

    latitude : DecimalField
        Координаты в формате "широта" (необязательно)

    longitude : DecimalField
        Координаты в формате "долгота" (необязательно)

    full_address : property
        Полный адрес в строковом формате (вычисляемое поле)
    ──────────────────────────────────────────────────────────────────────────────

    МЕТОДЫ:
    • get_full_address() - возвращает полный адрес в строковом формате
    • get_components() - возвращает словарь с компонентами адреса
    • validate_hierarchy() - проверяет целостность иерархии адреса
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Уникальный идентификатор"
    )

    # Основная иерархия адреса
    country = models.ForeignKey(
        "Country",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Страна",
        help_text="Страна (автоматически заполняется из иерархии)"
    )

    federal_district = models.ForeignKey(
        "FederalDistrict",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Федеральный округ",
        help_text="Федеральный округ (автоматически заполняется из иерархии)"
    )

    region = models.ForeignKey(
        "Region",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Регион",
        help_text="Регион (субъект федерации)"
    )

    city = models.ForeignKey(
        "City",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Город",
        help_text="Населенный пункт"
    )

    administrative_territory = models.ForeignKey(
        "AdministrativeTerritory",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Административный округ",
        help_text="Административный округ (для крупных городов)"
    )

    administrative_unit = models.ForeignKey(
        "AdministrativeTerritorialUnit",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Административно-территориальная единица",
        help_text="Район или округ в городе"
    )

    street = models.ForeignKey(
        "Street",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Улица",
        help_text="Улица, проспект, переулок и т.д."
    )

    house = models.ForeignKey(
        "House",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Дом",
        help_text="Дом (здание)"
    )

    building = models.ForeignKey(
        "Building",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Строение",
        help_text="Строение или корпус"
    )

    coordinates = models.ForeignKey(
        "Coordinates",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Координаты",
        help_text= "Координаты расположения магазина "
    )

    # Дополнительные поля
    microdistrict = models.CharField(
        "Микрорайон",
        max_length=100,
        blank=True,
        null=True,
        help_text="Микрорайон (если применимо)"
    )

    index = models.CharField(
        "Почтовый индекс",
        max_length=6,
        validators=[
            RegexValidator(r"^\d{6}$", "Индекс должен содержать 6 цифр"),
        ],
        blank=True,
        null=True,
        help_text="6-значный почтовый индекс"
    )

    latitude = models.CharField(
        "Широта",
	max_length=20,
        blank=True,
        null=True,
        help_text="Географическая широта места расположения объекта"
    )

    longitude = models.CharField(
        "Долгота",
        max_length=20,
        blank=True,
        null=True,
        help_text="Географическая долгота места расположения объекта"
    )

    class Meta:
        verbose_name = "Адрес"
        verbose_name_plural = "Адреса"
        db_table = "addresses_address"
        ordering = [
            'country__name',
            'region__name',
            'city__name',
            'street__name',
            'house__number',
            'building__number'
        ]

        indexes = [
            # Основные индексы для поиска
            BTreeIndex(fields=['country'], name='address_country_idx'),
            BTreeIndex(fields=['region'], name='address_region_idx'),
            BTreeIndex(fields=['city'], name='address_city_idx'),
            BTreeIndex(fields=['street'], name='address_street_idx'),
            BTreeIndex(fields=['house'], name='address_house_idx'),
            BTreeIndex(fields=['building'], name='address_building_idx'),

            # Индексы для часто используемых фильтров
            BTreeIndex(fields=['country', 'region'], name='address_country_region_idx'),
            BTreeIndex(fields=['region', 'city'], name='address_region_city_idx'),
            BTreeIndex(fields=['city', 'street'], name='address_city_street_idx'),

            # Индексы для поиска по текстовым полям
            GinIndex(
                fields=['index'],
                name='address_index_gin_idx',
                opclasses=['gin_trgm_ops']
            ),
        ]

    # ==========================================================================
    # СВОЙСТВА И ВЫЧИСЛЯЕМЫЕ ПОЛЯ
    # ==========================================================================

    @property
    @extend_schema_field(OpenApiTypes.STR)
    def full_address(self) -> str:
        """
        ПОЛНЫЙ АДРЕС в строковом формате.

        ВОЗВРАЩАЕТ:
            str: Полный адрес, собранный из всех заполненных компонентов

        ФОРМАТ:
            "Страна, Регион, Город, Улица, д. Номер, стр. Номер, Микрорайон"

        ПРИМЕР:
            >>> address.full_address
            'Россия, Московская область, Москва, ул. Ленина, д. 1, стр. А, Центральный микрорайон'

        ОСОБЕННОСТИ:
            • Пропускает пустые компоненты
            • Использует правильные форматы для типов (г., ул., д., стр.)
            • Автоматически заполняет недостающие компоненты из иерархии
        """
        # Собираем компоненты адреса
        components = []

        # Страна (если указана явно или может быть получена из иерархии)
        country = self._get_country()
        if country:
            components.append(country.name)

        # Регион (если указан явно или может быть получен из иерархии)
        region = self._get_region()
        if region:
            components.append(str(region))

        # Город (если указан явно или может быть получен из иерархии)
        city = self._get_city()
        if city:
            components.append(str(city))

        # Административная единица (если есть)
        if self.administrative_unit:
            components.append(str(self.administrative_unit))

        # Улица (если есть)
        if self.street:
            components.append(str(self.street))

        # Дом (если есть)
        if self.house:
            components.append(f"д. {self.house.number}")

        # Строение (если есть)
        if self.building:
            components.append(f"стр. {self.building.number}")

        # Микрорайон (если есть)
        if self.microdistrict:
            components.append(self.microdistrict)

        # Индекс (добавляем в начало, если есть)
        if self.index:
            components.insert(0, self.index)

        return ", ".join(filter(None, components))

    # ==========================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ==========================================================================

    def _get_country(self):
        """Получает страну из явного поля или из иерархии."""
        if self.country:
            return self.country
        elif self.federal_district:
            return self.federal_district.country
        elif self.region:
            return self.region.federal_district.country
        elif self.city:
            return self.city.region.federal_district.country
        return None

    def _get_region(self):
        """Получает регион из явного поля или из иерархии."""
        if self.region:
            return self.region
        elif self.city:
            return self.city.region
        return None

    def _get_city(self):
        """Получает город из явного поля."""
        return self.city

    def get_components(self):
        """
        ВОЗВРАЩАЕТ КОМПОНЕНТЫ АДРЕСА в виде словаря.

        ВОЗВРАЩАЕТ:
            dict: Словарь с компонентами адреса

        ПРИМЕР:
            >>> address.get_components()
            {
                'country': 'Россия',
                'region': 'Московская область',
                'city': 'Москва',
                'street': 'ул. Ленина',
                'house': '1',
                'building': 'А',
                'microdistrict': 'Центральный',
                'index': '101000',
                'latitude': '55.7558'
                'longitude': '37.6173'
            }
        """
        return {
            'country': self._get_country().name if self._get_country() else None,
            'region': str(self._get_region()) if self._get_region() else None,
            'city': str(self._get_city()) if self._get_city() else None,
            'administrative_territory': str(self.administrative_territory) if self.administrative_territory else None,
            'administrative_unit': str(self.administrative_unit) if self.administrative_unit else None,
            'street': str(self.street) if self.street else None,
            'house': self.house.number if self.house else None,
            'building': self.building.number if self.building else None,
            'microdistrict': self.microdistrict,
            'index': self.index,
            'coordinates': str(self.coordinates) if self.coordinates else None,
            'full_address': self.full_address
        }

    def validate_hierarchy(self):
        """
        ПРОВЕРЯЕТ ЦЕЛОСТНОСТЬ ИЕРАРХИИ адреса.

        ВЫПОЛНЯЕМЫЕ ПРОВЕРКИ:
        1. Если указано строение, должен быть указан дом
        2. Если указан дом, должна быть указана улица
        3. Если указана улица, должен быть указан город
        4. Если указан город, должен быть указан регион
        5. Если указан регион, должен быть указан федеральный округ (для России)

        ВОЗВРАЩАЕТ:
            bool: True если иерархия корректна

        ВЫБРАСЫВАЕТ ИСКЛЮЧЕНИЯ:
            ValidationError: При нарушении правил иерархии
        """

        errors = {}

        # Проверка 1: Строение требует дом
        if self.building and not self.house:
            errors['building'] = 'Для указания строения должен быть указан дом'

        # Проверка 2: Дом требует улицу
        if self.house and not self.street:
            errors['house'] = 'Для указания дома должна быть указана улица'

        # Проверка 3: Улица требует город
        if self.street and not self.city:
            errors['street'] = 'Для указания улицы должен быть указан город'

        # Проверка 4: Город требует регион
        if self.city and not self.region:
            errors['city'] = 'Для указания города должен быть указан регион'

        # Проверка 5: Регион требует федеральный округ (для России)
        if self.region and self.region.federal_district.country.name == "Россия" and not self.federal_district:
            # Автоматически заполняем федеральный округ из региона
            self.federal_district = self.region.federal_district
        elif self.federal_district and self.region and self.federal_district != self.region.federal_district:
            errors['federal_district'] = 'Федеральный округ не соответствует региону'

        if errors:
            raise ValidationError(errors)

        return True

    # ==========================================================================
    # МЕТОДЫ СОХРАНЕНИЯ И ОБРАБОТКИ
    # ==========================================================================

    def clean(self):
        """Валидация адреса перед сохранением."""
        # Проверяем целостность иерархии
        self.validate_hierarchy()

        # Автоматически заполняем недостающие поля из иерархии
        self._auto_fill_hierarchy()

        # Проверяем почтовый индекс
        if self.index and len(self.index) != 6:
            raise ValidationError({'index': 'Почтовый индекс должен содержать 6 цифр'})

    def _auto_fill_hierarchy(self):
        """Автоматически заполняет недостающие поля из иерархии."""
        # Заполняем страну, если она не указана, но есть другие компоненты
        if not self.country and self.region:
            self.country = self.region.federal_district.country

        # Заполняем федеральный округ для России
        if self.country and self.country.name == "Россия" and self.region and not self.federal_district:
            self.federal_district = self.region.federal_district

        # Заполняем регион из города
        if not self.region and self.city:
            self.region = self.city.region

    def save(self, *args, **kwargs):
        """Сохранение адреса с дополнительной обработкой."""
        # Валидация и автоматическое заполнение
        self.full_clean()

        # Проверяем существование такого же адреса
        existing = self._find_existing_address()
        if existing and self.pk != existing.pk:
            # Если нашли существующий адрес, возвращаем его
            # вместо создания нового (в зависимости от логики приложения)
            pass

        super().save(*args, **kwargs)

    def _find_existing_address(self):
        """
        ПОИСК СУЩЕСТВУЮЩЕГО АДРЕСА с такими же компонентами.

        ВОЗВРАЩАЕТ:
            Address or None: Существующий адрес или None

        ИСПОЛЬЗУЕТСЯ ДЛЯ:
            • Избежания дублирования адресов
            • Возврата существующего адреса вместо создания нового
        """
        from django.db.models import Q

        # Формируем условия поиска
        conditions = Q()

        if self.country:
            conditions &= Q(country=self.country)
        if self.region:
            conditions &= Q(region=self.region)
        if self.city:
            conditions &= Q(city=self.city)
        if self.administrative_territory:
            conditions &= Q(administrative_territory=self.administrative_territory)
        if self.administrative_unit:
            conditions &= Q(administrative_unit=self.administrative_unit)
        if self.street:
            conditions &= Q(street=self.street)
        if self.house:
            conditions &= Q(house=self.house)
        if self.building:
            conditions &= Q(building=self.building)
        if self.microdistrict:
            conditions &= Q(microdistrict=self.microdistrict)
        if self.index:
            conditions &= Q(index=self.index)

        # Ищем существующий адрес
        return Address.objects.filter(conditions).first()

    def __str__(self):
        """Строковое представление адреса."""
        return self.full_address or "Неполный адрес"
