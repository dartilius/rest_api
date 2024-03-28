from django.db import models
from backend.users.models import User


TYPES = (
    {"0": "Ad"},
    {"1": "Music"},
    {"2": "BG Image"},
    {"3": "BG Video"}
)

THEMES = (
    {"0": "Без тематики"},
    {"1": "Новый год"},
    {"2": "8 марта"},
    {"3": "9 мая"},
    {"4...": "всё остальное"}
)


class File(models.Model):

    uuid = models.UUIDField()
    name = models.CharField(max_length=254)
    hash = models.CharField()
    length = models.TimeField()
    size = models.IntegerField()
    owner = models.ForeignKey(
        User,
        verbose_name="Владелец",
        on_delete=models.CASCADE
    )
    file_type = models.Choices(TYPES)
    theme = models.Choices(THEMES)
    created = models.DateTimeField()
    
