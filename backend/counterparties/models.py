from django.db import models

from api import APIBaseObjectModel


class Counterparties(APIBaseObjectModel):
    code1c = models.CharField(
        verbose_name="Код из 1С", max_length=64, blank=True,
        null=True
    )
    name = models.CharField(
        max_length=64, blank=False, null=False, verbose_name="Наименование контрагента"
    )

    contact_persons = models.ManyToManyField(
        'contact_persons.Contact',
        related_name="counterparties",
        blank=True,
        verbose_name="Контактное лицо"
    )

    class Meta:
        db_table = "counterparties"
        verbose_name = "Контрагент"
        verbose_name_plural = "Контрагенты"

    def __str__(self):
        return f"{self.name}"
