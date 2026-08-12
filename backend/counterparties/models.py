"""
Модели для приложения counterparties.

ОПТИМИЗАЦИЯ:
───────────────────────────────────────────────────────────────────────────────
1. Оптимизировано свойство name для избежания N+1 запросов
2. Добавлена поддержка предзагруженных брендов через _prefetched_brands

СУЩЕСТВУЮЩИЕ ИНДЕКСЫ (не изменялись):
───────────────────────────────────────────────────────────────────────────────
- counterparty_name_gin_idx: поиск по ФИО (триграммы)
- counterparty_keyword_gin_idx: поиск по ключевому слову
- counterparty_desc_gin_idx: поиск по описанию
- keyword, description, inn, code1c, address, additional_name: обычные индексы
"""

from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.db.models.functions import Upper
from uuid import uuid4
from api import ContactInformation
from api.base_objects import UUIDPKField
from api import APIBaseObjectModel

TYPE_FL = {
    'IP': 'ИП',
    'FL': 'ФЛ',
    'SE': 'Самозанятый'
}

TYPE_ORG = {
    'AO': 'АО',
    'BF': 'БФ',
    'ZAO': 'ЗАО',
    'MAU': 'МАУ',
    'MP': 'МП',
    'OAO': 'ОАО',
    'OOO': 'ООО',
    'PAO': 'ПАО',
    'TCN': 'ТСН'
}

TYPE_OPF_DICT = {**TYPE_FL, **TYPE_ORG}
TYPE_OPF = [(key, value) for key, value in TYPE_OPF_DICT.items()]


class CounterpartyCategory(models.Model):
    """Справочник категорий контрагентов."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=64, unique=True, verbose_name="Название")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        db_table = "counterparty_categories"
        verbose_name = "Категория контрагента"
        verbose_name_plural = "Категории контрагентов"
        ordering = ("name",)
        indexes = [
            models.Index(
                Upper("name"),
                name="cp_category_name_ci_idx",
                condition=models.Q(is_active=True),
            ),
        ]

    def __str__(self):
        return self.name


class CounterpartyContactInfo(ContactInformation):
    """
    Контактная информация контрагента.

    АТРИБУТЫ:
        id (UUID): Уникальный идентификатор
        counterparty (ForeignKey): Контрагент
        type (str): Тип контакта (phone, mail, address, etc.)
        meaning (str): Значение контакта
        basic (bool): Основной контакт
        vidtel (str): Вид телефона
        vidmail (str): Вид почты
        comment (str): Комментарий
    """
    id = UUIDPKField()
    counterparty = models.ForeignKey(
        'Counterparty',
        on_delete=models.CASCADE,
        related_name="contacts",
        verbose_name="Контрагент"
    )

    class Meta:
        db_table = "counterparty_contact_info"
        verbose_name = "Контактная информация КА"
        verbose_name_plural = "Контактная информация КА"


class Counterparty(APIBaseObjectModel):
    """
    Контрагент (контрагентская единица).

    ОСНОВНЫЕ ПОЛЯ:
        code1c (str): Код из 1С
        opf (str): Организационно-правовая форма
        inn (str): ИНН
        first_name (str): Имя
        middle_name (str): Отчество
        last_name (str): Фамилия
        keyword (str): Ключевое слово (для юр. лиц)
        additional_name (str): Дополнительное название
        description (str): Описание
        broadcast (bool): Корпоративное вещание

    СВЯЗИ:
        brands (ManyToMany): Бренды контрагента
        contact_persons (ManyToMany): Контактные лица (пользователи)
        address (ForeignKey): Адрес
        owned_nomenclatures (related): Собственные номенклатуры
        rented_nomenclatures (related): Арендованные номенклатуры
    """

    name = None  # Переопределяем name из APIBaseObjectModel
    code1c = models.CharField(
        verbose_name="Код из 1С", max_length=64, blank=True,
        null=True, unique=True
    )

    opf = models.CharField(
        choices=TYPE_OPF,
        max_length=64,
        blank=True,
        null=True,
        verbose_name="ОПФ",
    )

    inn = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="ИНН",
        default=''
    )

    first_name = models.CharField(
        max_length=64, blank=False, null=False, verbose_name="Имя",
        default=''
    )

    middle_name = models.CharField(
        max_length=64, blank=True, null=False, verbose_name="Отчество",
        default=''
    )

    last_name = models.CharField(
        max_length=64, blank=False, null=False, verbose_name="Фамилия",
        default=''
    )

    description = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        default='',
        verbose_name="Описание"
    )

    keyword = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        default='',
        verbose_name="Ключевое слово"
    )

    additional_name = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        default='',
        verbose_name="Доп. название"
    )

    broadcast = models.BooleanField(
        default=False,
        verbose_name='Корпоративное вещание'
    )

    contact_persons = models.ManyToManyField(
        'users.CustomUser',
        related_name="counterparties",
        blank=True,
        verbose_name="Контактное лицо"
    )

    brands = models.ManyToManyField(
        'brands.Brand',
        verbose_name="Бренды КА",
        blank=True,
        related_name="counterparties"
    )

    categories = models.ManyToManyField(
        CounterpartyCategory,
        blank=True,
        related_name="counterparties",
        through="CounterpartyCategoryAssignment",
        through_fields=("counterparty", "category"),
        verbose_name="Категории контрагента",
    )

    address = models.ForeignKey(
        'addresses.Address',
        related_name='counterparties',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "counterparties"
        verbose_name = "Контрагент"
        verbose_name_plural = "Контрагенты"
        ordering = ("-created",)
        indexes = [
            GinIndex(
                name="counterparty_name_gin_idx",
                fields=["first_name", "middle_name", "last_name"],
                opclasses=["gin_trgm_ops", "gin_trgm_ops", "gin_trgm_ops"],
            ),
            GinIndex(
                name="counterparty_keyword_gin_idx",
                fields=["keyword"],
                opclasses=["gin_trgm_ops"],
            ),
            GinIndex(
                name="counterparty_desc_gin_idx",
                fields=["description"],
                opclasses=["gin_trgm_ops"],
            ),
            models.Index(fields=['keyword']),
            models.Index(fields=['description']),
            models.Index(fields=['inn']),
            models.Index(fields=['code1c']),
            models.Index(fields=['address']),
            models.Index(fields=['additional_name']),
        ]

    @property
    def is_broadcast(self):
        """Возвращает флаг корпоративного вещания."""
        return self.broadcast

    @property
    def name(self):
        """
        Возвращает полное имя контрагента в зависимости от ОПФ.

        ОПТИМИЗАЦИЯ:
        - Использует предзагруженные бренды через _prefetched_brands
        - Если _prefetched_brands отсутствует, делает запрос к БД

        Возвращает:
            str: Строка с именем контрагента
        """
        # Оптимизация: используем предзагруженные бренды, если они есть
        if hasattr(self, '_prefetched_brands'):
            brand_names = [b.name for b in self._prefetched_brands]
        else:
            brand_names = list(self.brands.values_list('name', flat=True))

        brand_list = ', '.join(brand_names) or ''
        desc = self.description or ''

        # Собираем ФИО
        fio = " ".join(filter(None, [self.first_name, self.middle_name, self.last_name]))

        # Если нет ОПФ
        if not self.opf:
            if self.keyword:
                details = ", ".join(filter(None, [desc, brand_list]))
                if details:
                    return f"{self.keyword} ({details})"
                return self.keyword
            return " ".join(filter(None, [desc, brand_list]))

        # Физлица
        if self.opf in TYPE_FL:
            if not brand_list and not desc:
                return fio
            if brand_list and not desc:
                return f"{fio}, ({brand_list})"
            if desc and not brand_list:
                return f"{fio}, ({desc})"
            return f"{fio}, ({brand_list}, {desc})"

        # Юр. лица
        if self.opf in TYPE_ORG:
            if not brand_list and not desc:
                return self.keyword or fio
            if brand_list and not desc:
                return f"{self.keyword}, ({brand_list})"
            if desc and not brand_list:
                return f"{self.keyword}, ({desc})"
            return f"{self.keyword}, ({brand_list}, {desc})"

        return fio

    def __str__(self):
        """Строковое представление контрагента."""
        return self.name


class CounterpartyCategoryAssignment(models.Model):
    """Назначение категории конкретному контрагенту."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    counterparty = models.ForeignKey(
        Counterparty,
        on_delete=models.CASCADE,
        related_name="category_assignments",
        verbose_name="Контрагент",
    )
    category = models.ForeignKey(
        CounterpartyCategory,
        on_delete=models.CASCADE,
        related_name="counterparty_assignments",
        verbose_name="Категория",
    )
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата назначения")

    class Meta:
        db_table = "counterparty_category_assignments"
        verbose_name = "Назначение категории контрагенту"
        verbose_name_plural = "Назначения категорий контрагентам"
        constraints = [
            models.UniqueConstraint(
                fields=("counterparty", "category"),
                name="unique_counterparty_category_assignment",
            ),
        ]
        indexes = [
            models.Index(
                fields=("category", "counterparty"),
                name="cp_category_lookup_idx",
            ),
        ]

    def __str__(self):
        return f"{self.counterparty} — {self.category}"

# from django.contrib.postgres.indexes import GinIndex
# from django.db import models
# from api import ContactInformation
# from api.base_objects import UUIDPKField
# from api import APIBaseObjectModel

# TYPE_FL = {
#     'IP': 'ИП',
#     'FL': 'ФЛ',
#     'SE': 'Самозанятый'
# }

# TYPE_ORG = {
#     'AO': 'АО',
#     'BF': 'БФ',
#     'ZAO': 'ЗАО',
#     'MAU': 'МАУ',
#     'MP': 'МП',
#     'OAO': 'ОАО',
#     'OOO': 'ООО',
#     'PAO': 'ПАО',
#     'TCN': 'ТСН'
# }

# # объединяем словари
# TYPE_OPF_DICT = {**TYPE_FL, **TYPE_ORG}

# # превращаем в корректные choices
# TYPE_OPF = [(key, value) for key, value in TYPE_OPF_DICT.items()]

# class CounterpartyContactInfo(ContactInformation):
#     id = UUIDPKField()
#     counterparty = models.ForeignKey(
#         'Counterparty',
#         on_delete=models.CASCADE,
#         related_name="contacts",
#         verbose_name="Контрагент"
#     )

#     class Meta:
#         db_table = "counterparty_contact_info"
#         verbose_name = "Контактная информация КА"
#         verbose_name_plural = "Контактная информация КА"


# class Counterparty(APIBaseObjectModel):
#     name = None
#     code1c = models.CharField(
#         verbose_name="Код из 1С", max_length=64, blank=True,
#         null=True, unique=True
#     )

#     opf = models.CharField(
#         choices=TYPE_OPF,
#         max_length=64,
#         blank=True,
#         null=True,
#         verbose_name="ОПФ",
#     )

#     inn = models.CharField(
#         max_length=64,
#         blank=True,
#         null=True,
#         verbose_name="ИНН",
#         default=''
#     )

#     first_name = models.CharField(
#         max_length=64, blank=False, null=False, verbose_name="Имя",
#         default=''
#     )

#     middle_name = models.CharField(
#         max_length=64, blank=True, null=False, verbose_name="Отчество",
#         default=''
#     )

#     last_name = models.CharField(
#         max_length=64, blank=False, null=False, verbose_name="Фамилия",
#         default=''
#     )

#     description = models.CharField(
#         max_length=256,
#         blank=True,
#         null=True,
#         default='',
#         verbose_name="Описание"
#     )

#     keyword = models.CharField(
#         max_length=256,
#         blank=True,
#         null=True,
#         default='',
#         verbose_name="Ключевое слово"
#     )

#     additional_name = models.CharField(
#         max_length=64,
#         blank=True,
#         null = True,
#         default='',
#         verbose_name="Доп. название"
#     )

#     broadcast = models.BooleanField(
#         default=False,
#         verbose_name='Корпоративное вещание'
#     )

#     contact_persons = models.ManyToManyField(
#         'users.CustomUser',
#         related_name="counterparties",
#         blank=True,
#         verbose_name="Контактное лицо"
#     )

#     brands = models.ManyToManyField(
#         'brands.Brand',
#         verbose_name="Бренды КА",
#         blank=True,
#         related_name="counterparties"
#     )

#     address = models.ForeignKey(
#         'addresses.Address',
#         related_name='counterparties',
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#     )


#     class Meta:
#         db_table = "counterparties"
#         verbose_name = "Контрагент"
#         verbose_name_plural = "Контрагенты"

#         ordering = ("-created",)
#         indexes = [
#             GinIndex(
#                 name="counterparty_name_gin_idx",
#                 fields=["first_name", "middle_name", "last_name"],
#                 opclasses=["gin_trgm_ops", "gin_trgm_ops", "gin_trgm_ops"],
#             ),
#             GinIndex(
#                 name="counterparty_keyword_gin_idx",
#                 fields=["keyword"],
#                 opclasses=["gin_trgm_ops"],
#             ),
#             GinIndex(
#                 name="counterparty_desc_gin_idx",
#                 fields=["description"],
#                 opclasses=["gin_trgm_ops"],
#             ),
#             models.Index(fields=['keyword']),
#             models.Index(fields=['description']),
#             models.Index(fields=['inn']),
#             models.Index(fields=['code1c']),
#             models.Index(fields=['address']),
#             # models.Index(fields=['contact_persons']),
#             models.Index(fields=['additional_name']),
#         ]

#     @property
#     def is_broadcast(self):
#         return self.broadcast

#     @property
#     def name(self):
#         # Собираем ФИО без двойных пробелов
#         fio = " ".join(filter(None, [self.first_name, self.middle_name, self.last_name]))

#         brand_list = ', '.join(self.brands.values_list('name', flat=True)) or ''
#         desc = self.description or ''

#         # Если нет opf, используем формат: keyword (desc, brand_list)
#         if not self.opf:
#             if self.keyword:
#                 details = ", ".join(filter(None, [desc, brand_list]))
#                 if details:
#                     return f"{self.keyword} ({details})"
#                 return self.keyword
#             # Если и keyword пустой
#             return " ".join(filter(None, [desc, brand_list]))

#         # Физлица
#         if self.opf in TYPE_FL:
#             # если брендов и описания нет → выводить только ФИО + ОПФ
#             if not brand_list and not desc:
#                 return f"{fio}"

#             # если бренды есть, но описания нет
#             if brand_list and not desc:
#                 return f"{fio}, ({brand_list})"

#             # если описание есть, но брендов нет
#             if desc and not brand_list:
#                 return f"{fio}, ({desc})"

#             # есть и бренды и описание
#             return f"{fio}, ({brand_list}, {desc})"

#         # Юр. лица
#         if self.opf in TYPE_ORG:
#             if not brand_list and not desc:
#                 return f"{self.keyword}"

#             if brand_list and not desc:
#                 return f"{self.keyword}, ({brand_list})"

#             if desc and not brand_list:
#                 return f"{self.keyword}, ({desc})"

#             return f"{self.keyword}, ({brand_list}, {desc})"

#         return fio

#     def __str__(self):
#         return f"{self.name}"
