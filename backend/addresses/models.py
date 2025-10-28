import uuid
from symtable import Class

from django.db import models
from django.core.validators import RegexValidator
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes


# --- 1. СТРАНА ---
class Country(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code1c = models.CharField("Код 1С", max_length=31, unique=True, null=True, blank=True)
    name = models.CharField("Название", max_length=255, unique=True)

    class Meta:
        verbose_name = "Страна"
        verbose_name_plural = "Страны"
        db_table = "addresses_country"

    def __str__(self):
        return self.name


# --- 2. ФЕДЕРАЛЬНЫЙ ОКРУГ ---
class FederalDistrict(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code1c = models.CharField("Код 1С", max_length=31, unique=True, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="federal_districts")
    name = models.CharField("Федеральный округ", max_length=255, unique=True)
    abbreviated_name = models.CharField("Сокращённое наименование", max_length=255, unique=True)

    class Meta:
        verbose_name = "Федеральный округ"
        verbose_name_plural = "Федеральные округа"
        db_table = "addresses_federal_district"

    def __str__(self):
        return self.name


# --- 3. ТИП РЕГИОНА ---
class TypeRegion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code1c = models.CharField(verbose_name="Код 1С", max_length=31, unique=True, null=True, blank=True)
    name = models.CharField(verbose_name="Тип региона", max_length=255, unique=True)
    abbreviated_name = models.CharField(verbose_name="Сокращённое наименование", max_length=50)
    show_before_name = models.BooleanField(verbose_name="Тип до наименования", default=False)
    skip_in_name = models.BooleanField(verbose_name="Не добавлять тип региона в наименование", default=False)

    class Meta:
        verbose_name = "Тип региона"
        verbose_name_plural = "Типы регионов"
        db_table = "addresses_type_region"

    def __str__(self):
        return self.name


# --- 4. ЧАСОВОЙ ПОЯС ---
class Timezone(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Наименование часового пояса", max_length=255, unique=True)
    offset_utc = models.IntegerField("Смещение относительно Гринвича (UTC)", help_text="Например: +3, +5, -2")
    offset_moscow = models.IntegerField("Смещение относительно московского времени", help_text="Например: +0, +2, -1")

    class Meta:
        verbose_name = "Часовой пояс"
        verbose_name_plural = "Часовые пояса"
        db_table = "addresses_timezone"

    def __str__(self):
        return f"UTC {self.offset_utc:+d} (Мск {self.offset_moscow:+d})"


# --- 5. РЕГИОН ---
class Region(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code1c = models.CharField("Код 1С", max_length=31, unique=True, null=True, blank=True)
    name = models.CharField("Наименование региона", max_length=255)
    abbreviated_name = models.CharField(verbose_name="Сокращённое наименование", max_length=255, blank=True, null=True)

    federal_district = models.ForeignKey(
        "FederalDistrict", on_delete=models.PROTECT, related_name="regions", verbose_name="Федеральный округ"
    )
    type_region = models.ForeignKey(
        "TypeRegion", on_delete=models.PROTECT, related_name="regions", verbose_name="Тип региона"
    )
    timezone = models.ForeignKey(
        "Timezone", on_delete=models.PROTECT, related_name="regions", verbose_name="Часовой пояс", null=True, blank=True
    )

    class Meta:
        verbose_name = "Регион"
        verbose_name_plural = "Регионы"
        unique_together = ("federal_district", "name")
        db_table = "addresses_region"

    def __str__(self):
        if self.type_region and not self.type_region.skip_in_name:
            if self.type_region.show_before_name:
                return f"{self.type_region.abbreviated_name} {self.name}"
            else:
                return f"{self.name} {self.type_region.abbreviated_name}"
        return self.name


# --- 6. ТИП НАСЕЛЕННОГО ПУНКТА ---
class LocalityType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code1c = models.CharField("Код 1С", max_length=31, unique=True, null=True, blank=True)
    name = models.CharField("Тип населённого пункта", max_length=255, unique=True)
    abbreviated_name = models.CharField("Сокращённое наименование", max_length=50, blank=True, null=True)
    show_before_name = models.BooleanField("Отображать тип до наименования", default=False)
    has_administrative_territory = models.BooleanField(
        "Имеет административный округ", default=False,
        help_text="Для городов федерального значения (Москва, Санкт-Петербург)"
    )

    class Meta:
        verbose_name = "Тип населённого пункта"
        verbose_name_plural = "Типы населённых пунктов"
        db_table = "addresses_locality_type"

    def __str__(self):
        return self.name

# --- 7. Города ---
class City(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code1c = models.CharField("Код 1С", max_length=31, unique=True, null=True, blank=True)
    name = models.CharField("Наименование города", max_length=255)
    region = models.ForeignKey("Region", on_delete=models.PROTECT, related_name="cities")
    locality_type = models.ForeignKey(
        "LocalityType", on_delete=models.PROTECT, related_name="cities", verbose_name="Тип населённого пункта"
    )
    timezone = models.ForeignKey(
        "Timezone", on_delete=models.PROTECT, related_name="cities", null=True, blank=True
    )
    has_atd = models.BooleanField("Наличие АТД", default=False)
    atd_type = models.CharField("Тип АТД", max_length=255, blank=True, null=True)
    has_administrative_territory = models.BooleanField(
        "Наличие административного округа", default=False,
        help_text="Отметить для городов, имеющих административные округа (например, Москва)"
    )

    class Meta:
        verbose_name = "Населённый пункт"
        verbose_name_plural = "Населённые пункты"
        unique_together = ("region", "name")
        db_table = "addresses_city"

    def __str__(self):
        if self.locality_type:
            prefix = self.locality_type.abbreviated_name or self.locality_type.name
            return f"{prefix} {self.name}" if self.locality_type.show_before_name else f"{self.name} {prefix}"
        return self.name


class AdministrativeTerritory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code1c = models.CharField("Код 1С", max_length=31, unique=True, null=True, blank=True)
    city = models.ForeignKey("City", on_delete=models.PROTECT, related_name="administrative_territories")
    name = models.CharField("Административный округ", max_length=255)

    class Meta:
        verbose_name = "Административный округ"
        verbose_name_plural = "Административные округа"
        unique_together = ("city", "name")
        db_table = "addresses_administrative_territory"

    def __str__(self):
        return self.name


class AdministrativeTerritorialUnit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code1c = models.CharField("Код 1С", max_length=31, unique=True, null=True, blank=True)
    name = models.CharField("Район / округ", max_length=255)
    city = models.ForeignKey("City", on_delete=models.PROTECT, related_name="territorial_units")
    administrative_territory = models.ForeignKey(
        "AdministrativeTerritory", on_delete=models.PROTECT, related_name="territorial_units",
        null=True, blank=True
    )

    class Meta:
        verbose_name = "Административно-территориальная единица"
        verbose_name_plural = "Административно-территориальные единицы"
        unique_together = ("city", "name")
        db_table = "addresses_administrative_territorial_unit"

    def __str__(self):
        return self.name


class StreetType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code1c = models.CharField("Код 1С", max_length=31, unique=True, null=True, blank=True)
    name = models.CharField("Тип улицы", max_length=255, unique=True)
    abbreviated_name = models.CharField("Сокращённое наименование", max_length=50, blank=True, null=True)
    show_before_name = models.BooleanField("Отображать тип до наименования", default=True)

    class Meta:
        verbose_name = "Тип улицы"
        verbose_name_plural = "Типы улиц"
        db_table = "addresses_street_type"

    def __str__(self):
        return self.name


class Street(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code1c = models.CharField("Код 1С", max_length=31, unique=True, null=True, blank=True)
    city = models.ForeignKey("City", on_delete=models.PROTECT, related_name="streets")
    street_type = models.ForeignKey("StreetType", on_delete=models.PROTECT, null=True, blank=True)
    name = models.CharField("Наименование улицы", max_length=255)

    class Meta:
        verbose_name = "Улица"
        verbose_name_plural = "Улицы"
        unique_together = ("city", "name")
        db_table = "addresses_street"

    def __str__(self):
        if self.street_type:
            prefix = self.street_type.abbreviated_name or self.street_type.name
            return f"{prefix} {self.name}" if self.street_type.show_before_name else f"{self.name} {prefix}"
        return self.name


class House(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code1c = models.CharField("Код 1С", max_length=31, unique=True, null=True, blank=True)
    street = models.ForeignKey("Street", on_delete=models.PROTECT, related_name="houses")
    number = models.CharField("Номер дома", max_length=31)

    class Meta:
        verbose_name = "Дом"
        verbose_name_plural = "Дома"
        unique_together = ("street", "number")
        db_table = "addresses_house"

    def __str__(self):
        return f"{self.street} {self.number}"


class Building(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code1c = models.CharField("Код 1С", max_length=31, unique=True, null=True, blank=True)
    house = models.ForeignKey("House", on_delete=models.PROTECT, related_name="buildings")
    number = models.CharField("Корпус / строение", max_length=31)

    class Meta:
        verbose_name = "Здание / строение"
        verbose_name_plural = "Здания / строения"
        unique_together = ("house", "number")
        db_table = "addresses_building"

    def __str__(self):
        return f"{self.house.street}, {self.house.number}, строение {self.number}"


class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code1c = models.CharField("Код 1С", max_length=31, unique=True, null=True, blank=True)

    country = models.ForeignKey("Country", on_delete=models.PROTECT, null=True, blank=True, verbose_name="Страна")
    federal_district = models.ForeignKey("FederalDistrict", on_delete=models.PROTECT, null=True, blank=True, verbose_name="Федеральный округ")
    region = models.ForeignKey("Region", on_delete=models.PROTECT, null=True, blank=True, verbose_name="Регион")
    city = models.ForeignKey("City", on_delete=models.PROTECT, null=True, blank=True, verbose_name="Город")
    administrative_territory = models.ForeignKey("AdministrativeTerritory", on_delete=models.PROTECT, null=True, blank=True, verbose_name="Административный округ")
    administrative_unit = models.ForeignKey("AdministrativeTerritorialUnit", on_delete=models.PROTECT, null=True, blank=True, verbose_name="Административно-территориальная единица")
    street = models.ForeignKey("Street", on_delete=models.PROTECT, null=True, blank=True, verbose_name="Улица")
    house = models.ForeignKey("House", on_delete=models.PROTECT, null=True, blank=True, verbose_name="Дом")
    building = models.ForeignKey("Building", on_delete=models.PROTECT, null=True, blank=True, verbose_name="Строение")

    microdistrict = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Микрорайон",
    )

    index = models.CharField(
        max_length=6,
        validators=[
            RegexValidator(r"^\d{6}$", "Индекс должен содержать 6 цифр"),
        ],
        blank=True,
        null=True,
        verbose_name="Почтовый индекс",
        help_text="6 цифр",
    )

    coordinates = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Координаты (широта, долгота)",
    )

    class Meta:
        verbose_name = "Адрес"
        verbose_name_plural = "Адреса"
        db_table = "addresses_address"

    @property
    @extend_schema_field(OpenApiTypes.STR)
    def full_address(self) -> str:
        parts = [
            self.country.name if self.country else "",
            self.region.name if self.region else "",
            self.city.name if self.city else "",
            self.street.__str__() if self.street else "",
            f"д. {self.house.number}" if self.house else "",
            f"стр. {self.building.number}" if self.building else "",
            self.microdistrict or "",
        ]
        return ", ".join(filter(None, parts))

    def __str__(self):
        return self.full_address
