import uuid
import re
from django.db import models
from django.core.exceptions import ValidationError
from nomenclatures.models import Nomenclature
from api import APIBaseObjectModel

# ---------- Справочники ----------
TYPE_OF_CONTACT = [
    ("CA", "Контактное лицо контрагента"),
    ("LK", "Личный контакт"),
    ("other", "Прочие"),
]

GENDER = [
    ("man", "Мужской"),
    ("women", "Женский"),
    ("tab", "Табуретка"),
]

CONTACTINFO = [
    ("address", "Адрес"),
    ("phone", "Телефон"),
    ("mail", "Адрес электронной почты"),
    ("web", "Веб-страница"),
    ("messenger", "Мессенджер"),
    ("other", "Другое"),
]

TYPEOFPHONE = [
    ("mobkl", "Телефон мобильный КЛ"),
    ("dop", "Дополнительный"),
    ("mobkldop", "Телефон дополнительный КЛ"),
]

TYPEMAIL = [
    ("rab", "E-mail рабочий КЛ"),
    ("dop", "E-mail дополнительный КЛ"),
    ("lich", "E-mail личный"),
]

# ---------- Основные модели ----------
class Contact(APIBaseObjectModel):
    """Контактное лицо (может быть связано с множеством номенклатур)."""
    vid = models.CharField(max_length=255, choices=TYPE_OF_CONTACT, default="CA", verbose_name="Вид")
    surname = models.CharField(max_length=100, verbose_name="Фамилия")
    name = models.CharField(max_length=100, verbose_name="Имя")
    patronymic = models.CharField(max_length=100, null=True, blank=True, verbose_name="Отчество")
    role = models.CharField(max_length=100, null=True, blank=True, verbose_name="Роль")
    job_title = models.CharField(max_length=100, null=True, blank=True, verbose_name="Должность")
    gender = models.CharField(max_length=255, choices=GENDER, default="man", verbose_name="Пол")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    other = models.CharField(max_length=255, null=True, blank=True, verbose_name="Прочее")

    class Meta:
        db_table = "contacts"
        verbose_name = "Контактное лицо"
        verbose_name_plural = "Контактные лица"

    def __str__(self):
        return f"{self.surname} {self.name}"


class ContactInformation(APIBaseObjectModel):
    """Контактная информация (телефон, почта, адрес и т.д.)."""
    basic = models.BooleanField(default=False, verbose_name="Основной")
    type = models.CharField(max_length=255, choices=CONTACTINFO, verbose_name="Тип")
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name="contact_information", verbose_name="Контактная информация")

    vidtel = models.CharField(max_length=255, null=True, blank=True, choices=TYPEOFPHONE, verbose_name="Вид телефона")
    vidmail = models.CharField(max_length=255, null=True, blank=True, choices=TYPEMAIL, verbose_name="Вид почты")

    meaning = models.CharField(max_length=255, verbose_name="Значение")
    ext = models.CharField(max_length=255, null=True, blank=True, verbose_name="Доб.")
    comment = models.CharField(max_length=255, null=True, blank=True, verbose_name="Комментарий")


    class Meta:
        db_table = "contact_information"
        verbose_name = "Контактная информация"
        verbose_name_plural = "Контактная информация"

    def __str__(self):
        return f"{self.type}: {self.meaning}"

    def clean(self):
        """Валидация значений в зависимости от типа."""
        if self.type == "phone":
            if not re.match(r"^\+?[0-9\-\(\) ]+$", self.meaning or ""):
                raise ValidationError("Значение должно быть корректным номером телефона.")
            if not self.vidtel:
                raise ValidationError("Для типа 'Телефон' нужно указать вид телефона.")
            self.vidmail = None
        elif self.type == "mail":
            if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", self.meaning or ""):
                raise ValidationError("Значение должно быть корректным адресом электронной почты.")
            if not self.vidmail:
                raise ValidationError("Для типа 'Почта' нужно указать вид почты.")
            self.vidtel = None
        else:
            self.vidtel = None
            self.vidmail = None
