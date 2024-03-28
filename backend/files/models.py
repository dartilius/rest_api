from django.db import models


class File(models.Model):

    uuid = models.UUIDField()
    owner = models.ForeignKey(
        User,
        verbose_name="Владелец",
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=254)
    hash = models.CharField()

