from uuid import uuid4
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils import timezone
from django_minio_backend import MinioBackend

""" чтобы soft-deleted объекты не возвращались """


class BrandManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


""" TODO: добавить поле уникального кода, для поиска id, если произошел сбой при создании. """


class Brand(models.Model):
    id = models.UUIDField(
        verbose_name="ИД", primary_key=True, editable=False, default=uuid4
    )

    name = models.CharField(
        max_length=64, blank=False, null=False, verbose_name="Наименование бренда", unique=True
    )
    description = models.TextField(
        max_length=255, blank=False, null=True, default=None, verbose_name="Описание бренда"
    )
    logotype = models.FileField(
        upload_to="brand_logo", storage=MinioBackend(bucket_name="local-media"),
        verbose_name="Логотип бренда"
    )
    created = models.DateTimeField(
        verbose_name="Дата создания", auto_now_add=True
    )
    is_deleted = models.BooleanField(
        default=False, verbose_name="Удалён"
    )
    deleted_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Дата удаления"
    )
    objects = BrandManager()  # фильтрует удалённые
    all_objects = models.Manager()  # возвращает все, включая удалённые

    class Meta:
        db_table = "brands"

        verbose_name = "Бренд"
        verbose_name_plural = "Бренды"
        ordering = ("-created",)
        constraints = [
            models.UniqueConstraint(
                fields=["name"],
                name="unique_brand_name",
                violation_error_message="Бренд с таким названием уже существует",
            )
        ]
        indexes = [
            GinIndex(
                name="brand_name_gin_idx",
                fields=["name"],
                opclasses=["gin_trgm_ops"],
            )
        ]

    """Мягкое удаление."""

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
