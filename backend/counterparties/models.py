from django.contrib.postgres.indexes import GinIndex
from django.db import models
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

# объединяем словари
TYPE_OPF_DICT = {**TYPE_FL, **TYPE_ORG}

# превращаем в корректные choices
TYPE_OPF = [(key, value) for key, value in TYPE_OPF_DICT.items()]

class CounterpartyContactInfo(ContactInformation):
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
    name = None
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
        null = True,
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
                name="counterparty_description_gin_idx",
                fields=["description"],
                opclasses=["gin_trgm_ops"],
            ),
            models.Index(fields=['keyword']),
            models.Index(fields=['description']),
            models.Index(fields=['inn']),
            models.Index(fields=['code1c']),
            models.Index(fields=['address']),
            models.Index(fields=['contact_persons']),
            models.Index(fields=['additional_name']),
        ]

    @property
    def is_broadcast(self):
        return self.broadcast

    @property
    def name(self):
        # Собираем ФИО без двойных пробелов
        fio = " ".join(filter(None, [self.first_name, self.middle_name, self.last_name]))

        brand_list = ', '.join(self.brands.values_list('name', flat=True)) or ''
        desc = self.description or ''

        # Если нет opf, используем формат: keyword (desc, brand_list)
        if not self.opf:
            if self.keyword:
                details = ", ".join(filter(None, [desc, brand_list]))
                if details:
                    return f"{self.keyword} ({details})"
                return self.keyword
            # Если и keyword пустой
            return " ".join(filter(None, [desc, brand_list]))

        # Физлица
        if self.opf in TYPE_FL:
            # если брендов и описания нет → выводить только ФИО + ОПФ
            if not brand_list and not desc:
                return f"{fio}"

            # если бренды есть, но описания нет
            if brand_list and not desc:
                return f"{fio}, ({brand_list})"

            # если описание есть, но брендов нет
            if desc and not brand_list:
                return f"{fio}, ({desc})"

            # есть и бренды и описание
            return f"{fio}, ({brand_list}, {desc})"

        # Юр. лица
        if self.opf in TYPE_ORG:
            if not brand_list and not desc:
                return f"{self.keyword}"

            if brand_list and not desc:
                return f"{self.keyword}, ({brand_list})"

            if desc and not brand_list:
                return f"{self.keyword}, ({desc})"

            return f"{self.keyword}, ({brand_list}, {desc})"

        return fio

    def __str__(self):
        return f"{self.name}"
