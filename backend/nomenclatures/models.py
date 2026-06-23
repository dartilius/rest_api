"""
Модели для приложения nomenclatures.

Данный модуль содержит модели для управления номенклатурами:
- Nomenclature: основная модель рабочей станции
- NomenclatureAvailability: статус доступности
- StatusHistory: история изменений статусов
- NomenclatureImage: фотографии номенклатур
- NomenclatureAddress: адреса номенклатур
- NomenclatureTenant: связи с арендаторами
- TypeOfPlace: типы мест размещения
- DiscountRule: правила скидок

ОПТИМИЗАЦИЯ SEARCH_VECTOR:
───────────────────────────────────────────────────────────────────────────────
1. Обновление только для for_web=True (экономия ресурсов)
2. Ограничение количества полей для индексации
3. Ограничение количества арендаторов (макс. 10)
4. Использование update вместо save для избежания рекурсии
5. Добавлен параметр force для принудительного обновления
6. Проверка наличия загруженных данных для избежания лишних запросов
"""

import hashlib
import re
from uuid import uuid4

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.validators import KeysValidator
from django.db import models
from django_minio_backend import MinioBackend
from django.utils.translation import gettext_lazy as _

from addresses.models import Address as AddressBook
from api import APIBaseObjectModel, Article, UUIDPKField


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


class TypeOfPlace(models.Model):
    """
    Тип места размещения номенклатуры.

    АТРИБУТЫ:
        name (str): Полное наименование
        tariff (str): Название для тарифа
        tariff_single (str): Название для тарифа в единственном числе
        abbreviation (str): Аббревиатура
        code1c (str): Код из 1С
        is_mall (bool): Является торговым центром
        is_active (bool): Активность
    """

    id = UUIDPKField()

    name = models.CharField(
        max_length=255,
        verbose_name="Полное наименование"
    )

    tariff = models.CharField(
        verbose_name="Для тарифа",
        blank=True,
        null=True,
    )

    tariff_single = models.CharField(
        verbose_name="Для тарифа в единственном числе",
        blank=True,
        null=True,
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


class NomenclatureTenant(models.Model):
    """
    Связь номенклатуры с арендатором.

    АТРИБУТЫ:
        nomenclature (ForeignKey): Номенклатура
        tenant (ForeignKey): Арендатор
        floor (str): Этаж
        atm (bool): Наличие банкомата/терминала
        brand (ForeignKey): Бренд арендатора
    """

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
    atm = models.BooleanField(verbose_name="Банкомат/терминал", default=False)
    brand = models.ForeignKey(
        'brands.Brand',
        on_delete=models.SET_NULL,
        verbose_name="Бренд арендатора",
        null=True,
        blank=True,
        related_name='brand_tenant',
    )

    class Meta:
        db_table = "nomenclature_tenant"
        indexes = [
            models.Index(fields=['nomenclature']),
            models.Index(fields=['tenant']),
            models.Index(fields=['tenant', 'nomenclature']),
            models.Index(fields=['brand']),
            models.Index(fields=['brand', 'tenant']),
        ]


class DiscountRule(models.Model):
    """
    Правило скидки по длительности размещения для конкретной номенклатуры.

    Пример:
        nomenclature=..., days_from=30, days_to=59, coefficient=0.90
        nomenclature=..., days_from=60, days_to=None, coefficient=0.85

    АТРИБУТЫ:
        nomenclature (ForeignKey): Номенклатура
        days_from (int): Начало периода (включительно)
        days_to (int): Конец периода (включительно, None = без верхней границы)
        coefficient (Decimal): Множитель цены
    """

    nomenclature = models.ForeignKey(
        "Nomenclature",
        on_delete=models.CASCADE,
        related_name="discount_rules",
        verbose_name="Номенклатура"
    )

    days_from = models.PositiveIntegerField(
        verbose_name="Дней (от)",
        help_text="Включительно"
    )

    days_to = models.PositiveIntegerField(
        verbose_name="Дней (до)",
        null=True,
        blank=True,
        help_text="Включительно. Пусто = без верхней границы"
    )

    coefficient = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        verbose_name="Коэффициент скидки",
        help_text="Множитель цены: 1.000 = без скидки, 0.900 = скидка 10%"
    )

    class Meta:
        db_table = "discount_rule"
        ordering = ("nomenclature", "days_from")
        verbose_name = "Правило скидки"
        verbose_name_plural = "Правила скидок"
        indexes = [
            models.Index(fields=["nomenclature", "days_from"]),
        ]

    def __str__(self):
        if self.days_to is not None:
            return f"{self.nomenclature} | {self.days_from}–{self.days_to} дн. → ×{self.coefficient}"
        return f"{self.nomenclature} | {self.days_from}+ дн. → ×{self.coefficient}"

    @classmethod
    def get_coefficient(cls, nomenclature_id, duration_days: int):
        """
        Возвращает коэффициент скидки для номенклатуры и количества дней.

        Аргументы:
            nomenclature_id (UUID): ID номенклатуры
            duration_days (int): Количество дней

        Возвращает:
            Decimal: Коэффициент скидки или 1 (без скидки)
        """
        rule = (
            cls.objects
            .filter(nomenclature_id=nomenclature_id)
            .filter(days_from__lte=duration_days)
            .filter(
                models.Q(days_to__gte=duration_days) |
                models.Q(days_to__isnull=True)
            )
            .order_by("-days_from")
            .first()
        )
        return rule.coefficient if rule else 1


class Nomenclature(APIBaseObjectModel):
    """
    Рабочая станция (номенклатура).

    ОСНОВНЫЕ ПОЛЯ:
        for_web (bool): Отображать в веб
        name (str): Название
        code1c (str): Код из 1С
        article (int): Артикул (автоинкремент)
        is_active (bool): Актуальность

    СВЯЗИ:
        brand (ForeignKey): Бренд номенклатуры
        legalEntity (ForeignKey): Юридическое лицо
        typeOfPlace (ForeignKey): Тип места размещения
        tenants (ManyToMany): Арендаторы (через NomenclatureTenant)
        responsible_* (ForeignKey): Ответственные лица

    НАСТРОЙКИ:
        settings (JSON): Настройки вещания
        timezone (str): Часовой пояс

    ПОИСК:
        search_vector (TextField): Денормализованное поле для полнотекстового поиска
        old_catalog_slug (SlugField): Старый slug для редиректов
    """

    for_web = models.BooleanField(
        default=False,
        verbose_name="Отображать в веб"
    )

    slots_per_hour = models.CharField(
        verbose_name="Кол-во выходов в час",
        null=True,
        blank=True,
        default=1
    )

    keys_validator = KeysValidator(
        keys=("mon", "tue", "wed", "thu", "fri", "sat", "sun"),
        strict=True
    )

    external_video_media = models.CharField(
        verbose_name="Видео носители (кол-во внеш.)",
        null=True,
        blank=True,
        default=""
    )
    external_audio_media = models.CharField(
        verbose_name="Аудио носители (кол-во внеш.)",
        null=True,
        blank=True,
        default=""
    )
    internal_video_media = models.CharField(
        verbose_name="Видео носители (кол-во внут.)",
        null=True,
        blank=True,
        default=""
    )
    internal_audio_media = models.CharField(
        verbose_name="Аудио носители (кол-во внут.)",
        null=True,
        blank=True,
        default=""
    )

    worktime_start = models.TimeField(
        auto_now_add=False,
        auto_now=False,
        verbose_name='Открытие',
        null=True,
        blank=True
    )

    worktime_end = models.TimeField(
        auto_now_add=False,
        auto_now=False,
        verbose_name="Закрытие",
        null=True,
        blank=True
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

    article = Article()

    description = models.TextField(
        blank=True, null=True, verbose_name="Описание"
    )

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

    old_catalog_slug = models.SlugField(
        max_length=512,
        blank=True,
        default='',
        verbose_name="Старый URL slug (каталог)",
        help_text="Slug из старой версии каталога для редиректов",
        db_index=True,
    )

    search_vector = models.TextField(
        blank=True,
        default='',
        verbose_name="Поисковый вектор",
        help_text="Денормализованное поле для полнотекстового поиска",
        db_index=True,
    )

    def update_search_vector(self, force=False):
        """
        Обновляет денормализованное поле поиска.

        Оптимизация:
        - Обновление только для for_web=True
        - Ограничение количества полей для индексации
        - Ограничение количества арендаторов (макс. 10)
        - Использование update вместо save для избежания рекурсии
        - Добавлен параметр force для принудительного обновления
        - Проверка наличия загруженных данных

        Аргументы:
            force (bool): Принудительное обновление даже для for_web=False
        """
        # Если не for_web и не force - очищаем search_vector
        if not self.for_web and not force:
            if self.search_vector:
                Nomenclature.objects.filter(pk=self.pk).update(search_vector='')
            return

        # Основные поля для поиска (приоритетные)
        parts = [
            self.name or '',
            self.code1c or '',
            self.id_rasb or '',
        ]

        # Дополнительные поля (менее приоритетные)
        additional_parts = [
            self.description or '',
            self.contentType or '',
        ]

        # Поля бренда
        if self.brand:
            additional_parts.append(self.brand.name or '')

        # Поля юридического лица
        if self.legalEntity:
            additional_parts.extend([
                self.legalEntity.keyword or '',
                self.legalEntity.additional_name or '',
            ])

        # Поля типа места
        if self.typeOfPlace:
            additional_parts.extend([
                self.typeOfPlace.name or '',
                self.typeOfPlace.abbreviation or '',
            ])

        # Ответственные пользователи (только ключевые поля)
        responsible_users = [
            self.responsible_ad,
            self.responsible_placement_marketing,
        ]

        for user in responsible_users:
            if user:
                additional_parts.append(f"{user.first_name} {user.last_name}".strip())

        # Арендаторы (ограничение 10 записей для производительности)
        # Проверяем, загружены ли данные, чтобы избежать лишнего запроса к БД
        if hasattr(self, 'nomenclature_tenants'):
            for relation in self.nomenclature_tenants.all()[:10]:
                if relation.tenant:
                    additional_parts.append(relation.tenant.keyword or '')
                if relation.brand:
                    additional_parts.append(relation.brand.name or '')

        # Объединяем все части
        all_parts = parts + additional_parts
        new_vector = ' '.join(filter(None, all_parts)).lower()

        # Обновляем только если изменилось
        if self.search_vector != new_vector:
            Nomenclature.objects.filter(pk=self.pk).update(search_vector=new_vector)

    def generate_old_catalog_slug(self):
        """
        Генерирует slug в формате старого каталога.

        Формат: <brand>_<place>_<region_name>_<region_type>_g_<city>_<street_type>_<street_name>_<house>
        Пример: lazurnyy_tts_irkutskaya_obl_g_irkutsk_ul_baykalskaya_202_6

        Возвращает:
            str: Сгенерированный slug (макс. 512 символов)
        """
        from transliterate import translit
        import re

        def to_slug(text):
            if not text:
                return ''
            try:
                text = translit(text, 'ru', reversed=True)
            except Exception:
                pass

            text = text.lower()

            replacements = {
                'irkutskaja': 'irkutskaya',
                'kemerovskaja': 'kemerovskaya',
                'novosibirskaja': 'novosibirskaya',
                'kirovskaja': 'kirovskaya',
                'penzenskaja': 'penzenskaya',
                'tyumenskaja': 'tyumenskaya',
                'kurganskaja': 'kurganskaya',
                'kostromskaja': 'kostromskaya',
                'orenburgskaja': 'orenburgskaya',
                'samarskaja': 'samarskaya',
                'sverdlovskaja': 'sverdlovskaya',
                'tomskaja': 'tomskaya',
                'bryanskaja': 'bryanskaya',
                'pskovskaja': 'pskovskaya',
                'sakhalinskaja': 'sakhalinskaya',
                'smolenskaja': 'smolenskaya',
                'tambovskaja': 'tambovskaya',
                'tulskaja': 'tulskaya',
                'vologodskaja': 'vologodskaya',
                'tverskaja': 'tverskaya',
                'vladimirskaja': 'vladimirskaya',
                'volgogradskaja': 'volgogradskaya',
                'yaroslavskaja': 'yaroslavskaya',
                'rostovskaja': 'rostovskaya',
                'evrejskaja': 'evreyskaya',
                'krasnojarskij': 'krasnoyarskiy',
                'krasnodarskij': 'krasnodarskiy',
                'zabajkalskij': 'zabaykalskiy',
                'permskij': 'permskiy',
                'primorskij': 'primorskiy',
                'khabarovskij': 'khabarovskiy',
                'khanty_mansiyskij': 'khanty_mansiyskiy',
                'chechenskaja': 'chechenskaya',
                'udmurtija': 'udmurtiya',
                'burjatija': 'buryatiya',
                'mordovija': 'mordoviya',
                'chuvashija': 'chuvashiya',
                'kalmykija': 'kalmykiya',
                'jakutija': 'yakutiya',
                'khakasija': 'khakasiya',
                'krasnojarsk': 'krasnoyarsk',
                'leninsk_kuzneckij': 'leninsk_kuznetskiy',
                'kuzneckij': 'kuznetskiy',
                'moskovskij': 'moskovskiy',
                'sibirskij': 'sibirskiy',
                'promyshlennovskoje': 'promyshlennovskoe',
                'sankt-peterburg': 'sankt_peterburg',
            }
            for bad, good in replacements.items():
                text = text.replace(bad, good)

            text = re.sub(r'[^\w\s-]', '', text.lower()).strip()
            return re.sub(r'[\s-]+', '_', text)

        parts = []

        if self.brand and self.brand.name:
            parts.append(to_slug(self.brand.name))

        if self.typeOfPlace:
            place = (
                self.typeOfPlace.abbreviation
                or self.typeOfPlace.tariff_single
                or self.typeOfPlace.name
                or ''
            )
            if place:
                parts.append(to_slug(place))

        try:
            nom_addr = self.address
            addr = nom_addr.address if nom_addr else None
        except Exception:
            addr = None

        if addr:
            if addr.region:
                region_name = to_slug(getattr(addr.region, 'name', '') or '')
                region_type = ''
                if hasattr(addr.region, 'type_region') and addr.region.type_region:
                    region_type = (
                        addr.region.type_region.abbreviated_name
                        or addr.region.type_region.name
                        or ''
                    )
                region_type = to_slug(region_type)
                if region_name and region_type:
                    parts.append(f"{region_name}_{region_type}")
                elif region_name:
                    parts.append(region_name)

            if addr.city and addr.city.name:
                parts.append(f"g_{to_slug(addr.city.name)}")

            if addr.street and addr.street.name:
                street_type = ''
                if hasattr(addr.street, 'street_type') and addr.street.street_type:
                    street_type = (
                        addr.street.street_type.abbreviated_name
                        or addr.street.street_type.name
                        or ''
                    )
                street_type = to_slug(street_type)
                street_name = to_slug(addr.street.name)
                if street_type and street_name:
                    parts.append(f"{street_type}_{street_name}")
                elif street_name:
                    parts.append(f"ul_{street_name}")

            if addr.house and addr.house.number:
                house = re.sub(r'[^a-zA-Z0-9_]+', '_', addr.house.number.strip())
                house = re.sub(r'_+', '_', house)
                if house:
                    parts.append(house)

        slug = '_'.join(filter(None, parts))
        return slug[:512]

    @property
    def brand_logo(self):
        """Возвращает логотип бренда."""
        return self.brand.logotype

    @property
    def type_of_place_display(self):
        """Возвращает отображаемое название типа места."""
        if not self.typeOfPlace:
            return None
        return self.typeOfPlace.abbreviation or self.typeOfPlace.name

    @property
    def formatted_address(self):
        """Возвращает отформатированный адрес."""
        addr = getattr(self, 'address', None)

        if not addr or not addr.address:
            return None

        a = addr.address

        if not a.city or not a.house:
            return None

        city = str(a.city)

        street_obj = a.street or getattr(a.house, 'street', None)

        street = str(street_obj) if street_obj else None

        house = f"д. {a.house.number}"

        building = (
            f"стр.{a.building.number}"
            if a.building else None
        )

        address_parts = filter(
            None,
            [city, street, house, building]
        )

        return ", ".join(address_parts)

    @property
    def name_for_front(self):
        """Возвращает название для фронтенда."""
        if not self.brand:
            return None

        address_str = self.formatted_address

        if not address_str:
            return None

        place = self.typeOfPlace

        if place:
            place_name = (
                place.abbreviation
                or place.tariff_single
                or place.name
            )
        else:
            place_name = ""

        return (
            f'Размещение ролика на радио '
            f'{place_name} "{self.brand.name}"\n '
            f'{address_str}'
        )

    def save(self, *args, **kwargs):
        """Сохраняет номенклатуру и генерирует old_catalog_slug при необходимости."""
        super().save(*args, **kwargs)
        if not self.old_catalog_slug:
            self.old_catalog_slug = self.generate_old_catalog_slug()
            type(self).objects.filter(pk=self.pk).update(
                old_catalog_slug=self.old_catalog_slug
            )

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
            GinIndex(
                name='nom_name_trgm_idx',
                fields=['name'],
                opclasses=['gin_trgm_ops']
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
            models.Index(fields=['responsible_technic']),
            models.Index(fields=['responsible_technic_on_address']),
            models.Index(fields=['responsible_placement_marketing']),
            models.Index(fields=['code1c']),
            models.Index(fields=['timezone']),
            models.Index(fields=['version']),
            models.Index(fields=['pricePerMonth']),
            models.Index(fields=['-created']),
            models.Index(fields=['brand', 'typeOfPlace']),
            models.Index(fields=['legalEntity', 'brand']),
            models.Index(fields=['search_vector']),
        ]


class NomenclatureAvailability(models.Model):
    """
    Текущая доступность номенклатуры.

    АТРИБУТЫ:
        last_answer_date (DateTime): Время последнего ответа
        client (OneToOneField): Номенклатура
        status (int): Статус доступности
    """

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
    """
    Адрес номенклатуры.

    АТРИБУТЫ:
        nomenclature (OneToOneField): Номенклатура
        address (ForeignKey): Адрес из справочника
    """

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
        verbose_name_plural = "Адреса Номенклатур"


class StatusHistory(models.Model):
    """
    История изменения доступности номенклатуры.

    АТРИБУТЫ:
        client (ForeignKey): Номенклатура
        change_time (DateTime): Время изменения статуса
        status (int): Новый статус
    """

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
    """Генерирует путь для сохранения изображения."""
    return f"{TYPES[instance.type]}/{filename}"


class NomenclatureImage(models.Model):
    """
    Фотографии экстерьера и интерьера номенклатур.

    АТРИБУТЫ:
        id (UUID): Уникальный идентификатор
        source (File): Файл изображения
        type (str): Тип фотографии
        created (DateTime): Дата создания
        nomenclature (ForeignKey): Номенклатура
        hash (str): MD5 хэш файла
    """

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
        """Сохраняет изображение и вычисляет MD5 хэш."""
        if self.source:
            file_data = self.source.read()
            self.hash = hashlib.md5(file_data).hexdigest()
            self.source.seek(0)
        super().save(*args, **kwargs)

    class Meta:
        db_table = "nomenclature_images"
        ordering = ("-created",)
        verbose_name = "Фотография номенклатуры"
        verbose_name_plural = "Фотографии номенклатур"

    def __str__(self):
        return f"{self.nomenclature} - {self.type}"

# import hashlib
# import re
# from uuid import uuid4
# from django.contrib.postgres.indexes import GinIndex
# from django.contrib.postgres.validators import KeysValidator
# from django.db import models
# from django_minio_backend import MinioBackend
# from django.utils.translation import gettext_lazy as _
# from addresses.models import Address as AddressBook
# from api import APIBaseObjectModel, Article, UUIDPKField

# TIMEZONES = {
#     "Etc/GMT+11": "UTC -11",
#     "Etc/GMT+10": "UTC -10",
#     "Etc/GMT+9": "UTC -9",
#     "Etc/GMT+8": "UTC -8",
#     "Etc/GMT+7": "UTC -7",
#     "Etc/GMT+6": "UTC -6",
#     "Etc/GMT+5": "UTC -5",
#     "Etc/GMT+4": "UTC -4",
#     "Etc/GMT+3": "UTC -3",
#     "Etc/GMT+2": "UTC -2",
#     "Etc/GMT+1": "UTC -1",
#     "Etc/GMT+0": "UTC",
#     "Etc/GMT-1": "UTC +1",
#     "Etc/GMT-2": "UTC +2",
#     "Etc/GMT-3": "UTC +3",
#     "Etc/GMT-4": "UTC +4",
#     "Etc/GMT-5": "UTC +5",
#     "Etc/GMT-6": "UTC +6",
#     "Etc/GMT-7": "UTC +7",
#     "Etc/GMT-8": "UTC +8",
#     "Etc/GMT-9": "UTC +9",
#     "Etc/GMT-10": "UTC +10",
#     "Etc/GMT-11": "UTC +11",
#     "Etc/GMT-12": "UTC +12",
# }

# TYPES = {
#     "interior": "Интерьер",
#     "exterior": "Экстерьер"
# }

# AVAILABLE_CONTENT_TYPES = {
#     "audio": "Аудио",
#     "video": "Видео",
#     "audio_video": "Аудио + Видео",
#     "audio_video_image": "Аудио + Видео + Картинка",
#     "video_image": "Видео + Картинка",
#     "audio_image": "Аудио + Картинка",
# }

# STATUSES = {
#     0: "Online",
#     1: "Offline 5+ minutes",
#     2: "Offline 1+ hour"
# }


# class TypeOfPlace(models.Model):
#     id = UUIDPKField()

#     name = models.CharField(
#         max_length=255,
#         verbose_name="Полное наименование"
#     )

#     tariff = models.CharField(
#         verbose_name="Для тарифа",
#         blank=True,
#         null=True,
#     )

#     tariff_single = models.CharField(
#         verbose_name="Для тарифа в единственном числе",
#         blank=True,
#         null=True,
#     )

#     abbreviation = models.CharField(
#         max_length=50,
#         blank=True,
#         null=True,
#         verbose_name="Аббревиатура"
#     )

#     code1c = models.CharField(
#         verbose_name="Код из 1С",
#         max_length=64,
#         blank=True,
#         null=True,
#         unique=True
#     )

#     is_mall = models.BooleanField(
#         default=False,
#         verbose_name="Является торговым центром"
#     )

#     is_active = models.BooleanField(
#         default=True,
#         verbose_name="Активно"
#     )

#     class Meta:
#         db_table = "type_of_place"
#         verbose_name = "Тип места"
#         verbose_name_plural = "Типы мест"



# class NomenclatureTenant(models.Model):
#     nomenclature = models.ForeignKey(
#         'Nomenclature',
#         on_delete=models.CASCADE,
#         related_name='nomenclature_tenants',
#         verbose_name="Номенклатура"
#     )
#     tenant = models.ForeignKey(
#         'counterparties.Counterparty',
#         on_delete=models.CASCADE,
#         related_name='tenant_nomenclatures',
#         verbose_name="Арендатор"
#     )
#     floor = models.CharField(max_length=10, blank=True, verbose_name="Этаж")
#     atm = models.BooleanField(verbose_name="Банкомат/терминал", default=False)
#     brand = models.ForeignKey(
#         'brands.Brand',
#         on_delete=models.SET_NULL,
#         verbose_name="Бренд арендатора",
#         null=True,
#         blank=True,
#         related_name='brand_tenant',
#     )

#     class Meta:
#         db_table = "nomenclature_tenant"

#         indexes = [
#             models.Index(fields=['nomenclature']),

#             models.Index(fields=['tenant']),

#             models.Index(fields=['tenant', 'nomenclature']),

#             models.Index(fields=['brand']),

#             models.Index(fields=['brand', 'tenant']),
#         ]

# class DiscountRule(models.Model):
#     """
#     Правило скидки по длительности размещения для конкретной номенклатуры.

#     Пример:
#         nomenclature=..., days_from=30, days_to=59, coefficient=0.90
#         nomenclature=..., days_from=60, days_to=None, coefficient=0.85
#     """

#     nomenclature = models.ForeignKey(
#         "Nomenclature",
#         on_delete=models.CASCADE,
#         related_name="discount_rules",
#         verbose_name="Номенклатура"
#     )

#     days_from = models.PositiveIntegerField(
#         verbose_name="Дней (от)",
#         help_text="Включительно"
#     )

#     days_to = models.PositiveIntegerField(
#         verbose_name="Дней (до)",
#         null=True,
#         blank=True,
#         help_text="Включительно. Пусто = без верхней границы"
#     )

#     coefficient = models.DecimalField(
#         max_digits=4,
#         decimal_places=3,
#         verbose_name="Коэффициент скидки",
#         help_text="Множитель цены: 1.000 = без скидки, 0.900 = скидка 10%"
#     )

#     class Meta:
#         db_table = "discount_rule"
#         ordering = ("nomenclature", "days_from")
#         verbose_name = "Правило скидки"
#         verbose_name_plural = "Правила скидок"
#         indexes = [
#             models.Index(fields=["nomenclature", "days_from"]),
#         ]

#     def __str__(self):
#         if self.days_to is not None:
#             return f"{self.nomenclature} | {self.days_from}–{self.days_to} дн. → ×{self.coefficient}"
#         return f"{self.nomenclature} | {self.days_from}+ дн. → ×{self.coefficient}"

#     @classmethod
#     def get_coefficient(cls, nomenclature_id, duration_days: int):
#         """
#         Возвращает коэффициент скидки для конкретной номенклатуры и кол-ва дней.
#         Если подходящего правила нет — возвращает 1 (без скидки).
#         """
#         rule = (
#             cls.objects
#             .filter(nomenclature_id=nomenclature_id)
#             .filter(days_from__lte=duration_days)
#             .filter(
#                 models.Q(days_to__gte=duration_days) |
#                 models.Q(days_to__isnull=True)
#             )
#             .order_by("-days_from")
#             .first()
#         )
#         return rule.coefficient if rule else 1

# class Nomenclature(APIBaseObjectModel):
#     """Рабочая станция."""

#     for_web = models.BooleanField(
#         default=False,
#         verbose_name="Отображать в веб"
#     )

#     slots_per_hour = models.CharField(
#         verbose_name="Кол-во выходов в час",
#         null=True,
#         blank=True,
#         default=1
#     )

#     keys_validator = KeysValidator(
#         keys=("mon", "tue", "wed", "thu", "fri", "sat", "sun"),
#         strict=True
#     )

#     external_video_media = models.CharField(
#         verbose_name="Видео носители (кол-во внеш.)",
#         null=True,
#         blank=True,
#         default=""
#     )
#     external_audio_media = models.CharField(
#         verbose_name="Аудио носители (кол-во внеш.)",
#         null=True,
#         blank=True,
#         default=""
#     )
#     internal_video_media = models.CharField(
#         verbose_name="Видео носители (кол-во внут.)",
#         null=True,
#         blank=True,
#         default=""
#     )
#     internal_audio_media = models.CharField(
#         verbose_name="Аудио носители (кол-во внут.)",
#         null=True,
#         blank=True,
#         default=""
#     )



#     worktime_start = models.TimeField(
#         auto_now_add=False,
#         auto_now=False,
#         verbose_name='Открытие',
#         null=True,
#         blank=True
#     )

#     worktime_end = models.TimeField(
#         auto_now_add=False,
#         auto_now=False,
#         verbose_name="Закртыие",
#         null=True,
#         blank=True
#     )

#     id_rasb = models.CharField(
#         null=True,
#         blank=True,
#         verbose_name="Id тачки",
#         default=''
#     )

#     square = models.CharField(
#         default="",
#         null=True,
#         blank=True,
#         verbose_name="Площадь"
#     )

#     possibility = models.CharField(
#         default="",
#         null=True,
#         blank=True,
#         verbose_name="Проходимость"
#     )

#     article = Article()

#     description = models.TextField(
#         blank=True, null=True, verbose_name="Описание"
#     )

#     responsible_radio = models.ForeignKey(
#         'users.CustomUser',
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="radio_nomenclature",
#         verbose_name="Ответственный за радио"
#     )

#     responsible_ad = models.ForeignKey(
#         'users.CustomUser',
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="ad_nomenclature",
#         verbose_name="Ответственный за размещение"
#     )

#     responsible_technic = models.ForeignKey(
#         'users.CustomUser',
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="technic_nomenclature",
#         verbose_name="Ответственный за технику"
#     )

#     responsible_technic_on_address = models.ForeignKey(
#         'users.CustomUser',
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="technic_on_address_nomenclature",
#         verbose_name="Ответственный за технику на адресе"
#     )

#     responsible_placement_marketing = models.ForeignKey(
#         'users.CustomUser',
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="placement_marketing_nomenclature",
#         verbose_name="Ответственный за маркетинг размещения"
#     )

#     timezone = models.CharField(
#         choices=TIMEZONES,
#         max_length=31,
#         verbose_name="Часовой пояс",
#         default="Etc/GMT-7",
#     )

#     code1c = models.CharField(
#         verbose_name="Код из 1С",
#         max_length=64,
#         blank=True,
#         null=True
#     )

#     version = models.CharField(
#         max_length=127,
#         verbose_name="Версия ПО"
#     )

#     settings = models.JSONField(
#         verbose_name="Настройки вещания",
#         validators=(keys_validator,),
#         blank=True,
#         default=dict
#     )

#     hw_info = models.JSONField(
#         verbose_name="Информация о железе",
#         blank=True, null=True
#     )

#     brand = models.ForeignKey(
#         'brands.Brand',
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         verbose_name="Бренд номенклатуры",
#         related_name="nomenclatures"
#     )

#     legalEntity = models.ForeignKey(
#         'counterparties.Counterparty',
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         verbose_name="Юр. лицо",
#         related_name="owned_nomenclatures"
#     )

#     tenants = models.ManyToManyField(
#         'counterparties.Counterparty',
#         through='NomenclatureTenant',
#         related_name="rented_nomenclatures",
#         verbose_name="Арендаторы"
#     )

#     contentType = models.CharField(
#         max_length=255,
#         choices=AVAILABLE_CONTENT_TYPES,
#         default="audio",
#     )

#     typeOfPlace = models.ForeignKey(
#         "TypeOfPlace",
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="type_nomenclature",
#         verbose_name="Тип места размещения"
#     )

#     pricePerMonth = models.DecimalField(
#         decimal_places=2,
#         max_digits=10,
#         verbose_name="Стоимость размещения в месяц",
#         default=0.0,
#     )

#     old_catalog_slug = models.SlugField(
#         max_length=512,
#         blank=True,
#         default='',
#         verbose_name="Старый URL slug (каталог)",
#         help_text="Slug из старой версии каталога для редиректов",
#         db_index=True,
#     )

#     search_vector = models.TextField(
#         blank=True,
#         default='',
#         verbose_name="Поисковый вектор",
#         help_text="Денормализованное поле для полнотекстового поиска",
#         db_index=True,
#     )

#     # nomenclatures/models.py

#     def update_search_vector(self):
#         """Обновляет денормализованное поле поиска только для for_web=True."""
#         if not self.for_web:
#             if self.search_vector:
#                 # Используем update вместо save, чтобы не вызывать сигналы
#                 Nomenclature.objects.filter(pk=self.pk).update(search_vector='')
#             return

#         parts = [
#             self.name or '',
#             self.code1c or '',
#             self.description or '',
#             self.id_rasb or '',
#             self.square or '',
#             self.possibility or '',
#             self.contentType or '',
#         ]

#         if self.brand:
#             parts.extend([
#                 self.brand.name or '',
#                 self.brand.code1c or '',
#             ])

#         if self.legalEntity:
#             parts.extend([
#                 self.legalEntity.first_name or '',
#                 self.legalEntity.middle_name or '',
#                 self.legalEntity.last_name or '',
#                 self.legalEntity.keyword or '',
#                 self.legalEntity.additional_name or '',
#             ])

#         if self.typeOfPlace:
#             parts.extend([
#                 self.typeOfPlace.name or '',
#                 self.typeOfPlace.abbreviation or '',
#                 self.typeOfPlace.code1c or '',
#                 self.typeOfPlace.tariff or '',
#                 self.typeOfPlace.tariff_single or '',
#             ])

#         responsible_users = [
#             self.responsible_radio,
#             self.responsible_ad,
#             self.responsible_technic,
#             self.responsible_technic_on_address,
#             self.responsible_placement_marketing,
#         ]

#         for user in responsible_users:
#             if user:
#                 parts.extend([
#                     user.email or '',
#                     user.first_name or '',
#                     user.last_name or '',
#                     f'{user.first_name} {user.last_name}'.strip(),
#                 ])

#         for relation in self.nomenclature_tenants.all():
#             if relation.tenant:
#                 parts.extend([
#                     relation.tenant.first_name or '',
#                     relation.tenant.middle_name or '',
#                     relation.tenant.last_name or '',
#                     relation.tenant.keyword or '',
#                     relation.tenant.additional_name or '',
#                 ])
#             if relation.brand:
#                 parts.extend([
#                     relation.brand.name or '',
#                     relation.brand.code1c or '',
#                 ])

#         new_vector = ' '.join(filter(None, parts)).lower()

#         # Используем update вместо save, чтобы избежать рекурсии
#         Nomenclature.objects.filter(pk=self.pk).update(search_vector=new_vector)

#     def generate_old_catalog_slug(self):
#         """
#         Генерирует slug в формате старого каталога.
#         Формат: <brand>_<place>_<region_name>_<region_type>_g_<city>_<street_type>_<street_name>_<house>
#         Пример: lazurnyy_tts_irkutskaya_obl_g_irkutsk_ul_baykalskaya_202_6
#         """
#         from transliterate import translit
#         import re

#         def to_slug(text):
#             if not text:
#                 return ''
#             try:
#                 text = translit(text, 'ru', reversed=True)
#             except Exception:
#                 pass

#             text = text.lower()


#             # Замены для соответствия старым URL (особенности ручной транслитерации)
#             replacements = {
#                 # Области (окончание "ская" → "skaya")
#                 'irkutskaja': 'irkutskaya',
#                 'kemerovskaja': 'kemerovskaya',
#                 'novosibirskaja': 'novosibirskaya',
#                 'kirovskaja': 'kirovskaya',
#                 'penzenskaja': 'penzenskaya',
#                 'tyumenskaja': 'tyumenskaya',
#                 'kurganskaja': 'kurganskaya',
#                 'kostromskaja': 'kostromskaya',
#                 'orenburgskaja': 'orenburgskaya',
#                 'samarskaja': 'samarskaya',
#                 'sverdlovskaja': 'sverdlovskaya',
#                 'tomskaja': 'tomskaya',
#                 'bryanskaja': 'bryanskaya',
#                 'pskovskaja': 'pskovskaya',
#                 'sakhalinskaja': 'sakhalinskaya',
#                 'smolenskaja': 'smolenskaya',
#                 'tambovskaja': 'tambovskaya',
#                 'tulskaja': 'tulskaya',
#                 'vologodskaja': 'vologodskaya',
#                 'tverskaja': 'tverskaya',
#                 'vladimirskaja': 'vladimirskaya',
#                 'volgogradskaja': 'volgogradskaya',
#                 'yaroslavskaja': 'yaroslavskaya',
#                 'rostovskaja': 'rostovskaya',
#                 'evrejskaja': 'evreyskaya',           # Еврейская АО

#                 # Края (окончание "ий" → "ий" с y)
#                 'krasnojarskij': 'krasnoyarskiy',
#                 'krasnodarskij': 'krasnodarskiy',
#                 'zabajkalskij': 'zabaykalskiy',
#                 'permskij': 'permskiy',
#                 'primorskij': 'primorskiy',
#                 'khabarovskij': 'khabarovskiy',

#                 # Автономные округа
#                 'khanty_mansiyskij': 'khanty_mansiyskiy',

#                 # Республики (названия-прилагательные и существительные)
#                 'chechenskaja': 'chechenskaya',
#                 'udmurtija': 'udmurtiya',
#                 'burjatija': 'buryatiya',
#                 'mordovija': 'mordoviya',
#                 'chuvashija': 'chuvashiya',
#                 'kalmykija': 'kalmykiya',
#                 'jakutija': 'yakutiya',
#                 'khakasija': 'khakasiya',

#                 # Города и прочие значимые слова
#                 'krasnojarsk': 'krasnoyarsk',
#                 'leninsk_kuzneckij': 'leninsk_kuznetskiy',
#                 'kuzneckij': 'kuznetskiy',
#                 'moskovskij': 'moskovskiy',
#                 'sibirskij': 'sibirskiy',
#                 'promyshlennovskoje': 'promyshlennovskoe',
#                 'sankt-peterburg': 'sankt_peterburg',   # дефис → подчёркивание
#             }
#             for bad, good in replacements.items():
#                 text = text.replace(bad, good)

#             # Оставляем только буквы, цифры, пробелы, дефисы, подчёркивания
#             text = re.sub(r'[^\w\s-]', '', text.lower()).strip()
#             # Пробелы и дефисы заменяем на подчёркивания
#             return re.sub(r'[\s-]+', '_', text)

#         parts = []

#         # 1) Бренд
#         if self.brand and self.brand.name:
#             parts.append(to_slug(self.brand.name))

#         # 2) Тип места (abbreviation > tariff_single > name)
#         if self.typeOfPlace:
#             place = (
#                 self.typeOfPlace.abbreviation          # сначала аббревиатура (ТЦ -> tts)
#                 or self.typeOfPlace.tariff_single
#                 or self.typeOfPlace.name
#                 or ''
#             )
#             if place:
#                 parts.append(to_slug(place))

#         # 3) Адресные компоненты через NomenclatureAddress
#         try:
#             nom_addr = self.address
#             addr = nom_addr.address if nom_addr else None
#         except Exception:
#             addr = None

#         if addr:
#             # Регион: <название>_<тип>  (например "irkutskaya_obl")
#             if addr.region:
#                 region_name = to_slug(getattr(addr.region, 'name', '') or '')
#                 region_type = ''
#                 if hasattr(addr.region, 'type_region') and addr.region.type_region:
#                     region_type = (
#                         addr.region.type_region.abbreviated_name
#                         or addr.region.type_region.name
#                         or ''
#                     )
#                 region_type = to_slug(region_type)
#                 if region_name and region_type:
#                     parts.append(f"{region_name}_{region_type}")
#                 elif region_name:
#                     parts.append(region_name)

#             # Город: префикс "g_"
#             if addr.city and addr.city.name:
#                 parts.append(f"g_{to_slug(addr.city.name)}")

#             # Улица: тип + название
#             if addr.street and addr.street.name:
#                 street_type = ''
#                 if hasattr(addr.street, 'street_type') and addr.street.street_type:
#                     street_type = (
#                         addr.street.street_type.abbreviated_name
#                         or addr.street.street_type.name
#                         or ''
#                     )
#                 street_type = to_slug(street_type)
#                 street_name = to_slug(addr.street.name)
#                 if street_type and street_name:
#                     parts.append(f"{street_type}_{street_name}")
#                 elif street_name:
#                     # Если тип не задан, используем стандартное 'ul' (улица)
#                     parts.append(f"ul_{street_name}")

#             # Дом: номер с заменой разделителей на подчёркивания
#             if addr.house and addr.house.number:
#                 house = re.sub(r'[^a-zA-Z0-9_]+', '_', addr.house.number.strip())
#                 house = re.sub(r'_+', '_', house)  # убираем дублирование подчёркиваний
#                 if house:
#                     parts.append(house)

#         slug = '_'.join(filter(None, parts))
#         # Обрезаем до максимальной длины поля (512 символов)
#         return slug[:512]

#     @property
#     def brand_logo(self):
#         return self.brand.logotype

#     @property
#     def type_of_place_display(self):
#         if not self.typeOfPlace:
#             return None
#         return self.typeOfPlace.abbreviation or self.typeOfPlace.name

#     @property
#     def formatted_address(self):
#         addr = getattr(self, 'address', None)

#         if not addr or not addr.address:
#             return None

#         a = addr.address

#         if not a.city or not a.house:
#             return None

#         city = str(a.city)

#         street_obj = a.street or getattr(a.house, 'street', None)

#         street = str(street_obj) if street_obj else None

#         house = f"д. {a.house.number}"

#         building = (
#             f"стр.{a.building.number}"
#             if a.building else None
#         )

#         address_parts = filter(
#             None,
#             [city, street, house, building]
#         )

#         return ", ".join(address_parts)

#     @property
#     def name_for_front(self):
#         if not self.brand:
#             return None

#         address_str = self.formatted_address

#         if not address_str:
#             return None

#         place = self.typeOfPlace

#         if place:
#             place_name = (
#                     place.abbreviation
#                     or place.tariff_single
#                     or place.name
#             )
#         else:
#             place_name = ""

#         return (
#             f'Размещение ролика на радио '
#             f'{place_name} "{self.brand.name}"\n '
#             f'{address_str}'

#         )

#     def save(self, *args, **kwargs):
#         super().save(*args, **kwargs)
#         if not self.old_catalog_slug:
#             self.old_catalog_slug = self.generate_old_catalog_slug()
#             type(self).objects.filter(pk=self.pk).update(
#                 old_catalog_slug=self.old_catalog_slug
#             )

#     def __str__(self):
#         return self.name

#     class Meta:
#         db_table = "nomenclature"
#         verbose_name = "Номенклатура"
#         verbose_name_plural = "Номенклатуры"
#         constraints = [
#             models.UniqueConstraint(
#                 fields=["code1c"],
#                 name="unique_nomenclature_name",
#                 violation_error_message="Номенклатура с таким кодом уже существует",
#             )
#         ]
#         indexes = [
#             GinIndex(
#                 name='nom_name_trgm_idx',
#                      fields=['name'],
#                      opclasses=['gin_trgm_ops']
#             ),
#             GinIndex(
#                 name="nomenclature_name_gin_idx",
#                 fields=["name"],
#                 opclasses=["gin_trgm_ops"],
#             ),
#             GinIndex(
#                 name="nomenclature_code1c_gin_idx",
#                 fields=["code1c"],
#                 opclasses=["gin_trgm_ops"],
#             ),
#             GinIndex(
#                 name="nomenclature_version_gin_idx",
#                 fields=["version"],
#                 opclasses=["gin_trgm_ops"],
#             ),
#             GinIndex(fields=['settings'], name='settings_gin_idx'),
#             models.Index(fields=['typeOfPlace']),
#             models.Index(fields=['responsible_radio']),
#             models.Index(fields=['responsible_ad']),
#             models.Index(
#                 fields=['brand'],
#                 name='idx_active_brand',
#                 condition=models.Q(is_active=True)
#             ),
#             models.Index(fields=['legalEntity']),

#             # ДОБАВЛЯЕМ НЕДОСТАЮЩИЕ FK
#             models.Index(fields=['responsible_technic']),
#             models.Index(fields=['responsible_technic_on_address']),
#             models.Index(fields=['responsible_placement_marketing']),

#             # ИНДЕКСЫ ДЛЯ ПОИСКА ПО ТОЧНОМУ СОВПАДЕНИЮ
#             models.Index(fields=['code1c']),
#             models.Index(fields=['timezone']),
#             models.Index(fields=['version']),

#             # ИНДЕКС ДЛЯ СОРТИРОВКИ
#             models.Index(fields=['pricePerMonth']),
#             models.Index(fields=['-created']),

#             # СОСТАВНЫЕ ИНДЕКСЫ ДЛЯ ЧАСТЫХ КОМБИНАЦИЙ
#             models.Index(fields=['brand', 'typeOfPlace']),
#             models.Index(fields=['legalEntity', 'brand']),
#             models.Index(fields=['search_vector']),

#         ]


# class NomenclatureAvailability(models.Model):
#     """Текущая доступность."""

#     last_answer_date = models.DateTimeField(
#         verbose_name="Время последнего ответа",
#     )

#     client = models.OneToOneField(
#         Nomenclature,
#         verbose_name="Рабочая станция",
#         related_name="availability",
#         on_delete=models.CASCADE,
#     )

#     status = models.PositiveSmallIntegerField(
#         choices=STATUSES, verbose_name="Статус", default=2
#     )

#     class Meta:
#         db_table = "availability"
#         ordering = ("-last_answer_date",)
#         verbose_name = "Время последнего ответа"
#         verbose_name_plural = "Время последнего ответа"

#     def __str__(self):
#         return f"{self.last_answer_date}"


# class NomenclatureAddress(models.Model):
#     nomenclature = models.OneToOneField(
#         Nomenclature,
#         verbose_name="Номенклатура",
#         primary_key=True,
#         on_delete=models.CASCADE,
#         related_name="address",
#     )
#     address = models.ForeignKey(
#         AddressBook,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         verbose_name="Адрес из справочника",
#     )

#     class Meta:
#         db_table = "nomenclature_addresses"
#         verbose_name = "Адрес Номенклатуры"
#         verbose_name_plural = "Ареса Номенклатур"


# class StatusHistory(models.Model):
#     """История изменения доступности."""

#     client = models.ForeignKey(
#         Nomenclature,
#         verbose_name="Рабочая станция",
#         related_name="history",
#         on_delete=models.CASCADE,
#     )
#     change_time = models.DateTimeField(
#         verbose_name="Время изменения статуса",
#         auto_now_add=True
#     )
#     status = models.PositiveSmallIntegerField(
#         choices=STATUSES, verbose_name="Статус"
#     )

#     class Meta:
#         db_table = "status_history"
#         ordering = ("-change_time",)
#         verbose_name = "История доступности"
#         verbose_name_plural = "История доступности"

#     def __str__(self):
#         return (
#             f"{self.change_time:%Y-%m-%d %H:%M:%S}: "
#             f"статус {self.client.name} "
#             f"изменился на {STATUSES[self.status][1]}"
#         )


# def media_path(instance, filename):
#     return f"{TYPES[instance.type]}/{filename}"


# class NomenclatureImage(models.Model):
#     """Фотографии экстерьера и интерьера номенклатур."""

#     class PhotoType(models.TextChoices):
#         INTERIOR = "interior", _("Интерьер")
#         EXTERIOR = "exterior", _("Экстерьер")
#         SIGNAGE = "signage", _("Вывеска")
#         INSTALLATION = "installation", _("Установка")

#     id = models.UUIDField(
#         primary_key=True,
#         default=uuid4,
#         editable=False,
#         verbose_name="ИД"
#     )

#     source = models.FileField(
#         verbose_name="Файл",
#         upload_to=media_path,
#         storage=MinioBackend(bucket_name="local-media"),
#     )

#     type = models.CharField(
#         max_length=31,
#         choices=PhotoType.choices,
#         verbose_name="Тип фотографии"
#     )

#     created = models.DateTimeField(
#         auto_now_add=True,
#         verbose_name="Дата создания"
#     )

#     nomenclature = models.ForeignKey(
#         "Nomenclature",
#         related_name="images",
#         on_delete=models.CASCADE,
#         verbose_name="Номенклатура",
#     )

#     hash = models.CharField(max_length=64, editable=False, db_index=True)

#     def save(self, *args, **kwargs):
#         if self.source:
#             # читаем файл в бинарном режиме и считаем MD5
#             file_data = self.source.read()
#             self.hash = hashlib.md5(file_data).hexdigest()
#             # возвращаем курсор файла в начало, иначе Django не сможет сохранить
#             self.source.seek(0)
#         super().save(*args, **kwargs)

#     class Meta:
#         db_table = "nomenclature_images"
#         ordering = ("-created",)
#         verbose_name = "Фотография номенклатуры"
#         verbose_name_plural = "Фотографии номенклатур"

#     def __str__(self):
#         return f"{self.nomenclature} - {self.type}"
