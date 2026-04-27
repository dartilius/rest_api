from django.db import models

class Feedback(models.Model):
    name = models.CharField(
        verbose_name="Имя",
        null=False,
        blank=False,
    )
    phone = models.CharField(
        verbose_name="Телефон",
        null=False,
        blank=False,
    )
    email = models.CharField(
        verbose_name="Почта",
        null=False,
        blank=False,
    )
    message = models.CharField(
        verbose_name="Текст обращения",
        null=False,
        blank=False,
    )
    created = models.DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True,
    )

    class Meta:
        db_table = "feedback"
        verbose_name = "Обратная связь"
        verbose_name_plural = "Обратные связи"
        ordering = ("-created",)