from django.db import models
from backend.nomenclatures.models import Nomenclature
from backend.users.models import User

TYPES = [
    (0, "DOWNLOADS"),
    (1, "PLAYLIST.MUSIC"),
    (2, "UPDATE"),
    (3, "DEL.TASK"),
    (4, "Всё остальное")
]

STATUSES = [
    (0, "Ожидает обработки"),
    (1, "Выполнена"),
    (2, "Ошибка"),
    (3, "Отменена"),
    (4, "Всё стальное")
]


class Task(models.Model):
    """tasks."""

    id = models.UUIDField(
        primary_key=True,
        unique=True,
        editable=False,
        verbose_name="Уникальный идентификатор"
    )
    client = models.ForeignKey(
        Nomenclature,
        related_name="tasks",
        on_delete=models.CASCADE,
        verbose_name="Целевая рабочая станция"
    )
    owner = models.ForeignKey(
        User,
        related_name="files",
        verbose_name="Кто создал",
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    parameters = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Тело"
    )
    task_type = models.CharField(
        choices=TYPES,
        max_length=50,
        verbose_name="Тип"
    )
    status = models.CharField(
        choices=STATUSES,
        max_length=50,
        verbose_name="Статус"
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время создания"
    )
    updated = models.DateTimeField(
        verbose_name="Время выполнения"
    )
