from uuid import uuid4
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils import timezone
from django_minio_backend import MinioBackend
from django.utils.text import slugify
from transliterate import translit
import re
""" чтобы soft-deleted объекты не возвращались """

class BrandManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


""" TODO: добавить поле уникального кода, для поиска id, если произошел сбой при создании. """


class Brand(models.Model):
    id = models.UUIDField(
        verbose_name="ИД", primary_key=True, editable=False, default=uuid4
    )
    slug = models.SlugField(
        max_length=100, unique=True, blank=True, null=True,
        verbose_name="Slug"
    )
    code1c = models.CharField(
        verbose_name="Код из 1С", max_length=64, blank=True, null=True, unique=True
    )
    name = models.CharField(
        max_length=64, blank=False, null=False, verbose_name="Наименование бренда"
    )
    description = models.TextField(
        max_length=255, blank=True, null=True, default=None, verbose_name="Описание бренда"
    )
    logotype = models.FileField(
        upload_to="brand_logo", storage=MinioBackend(bucket_name="local-media"),
        verbose_name="Логотип бренда", null=True, blank=True
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
        indexes = [
            GinIndex(
                name="brand_name_gin_idx",
                fields=["name"],
                opclasses=["gin_trgm_ops"],
            ),
            models.Index(fields=["name"]),
            models.Index(fields=["description"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_slug()
        super().save(*args, **kwargs)

    def _generate_slug(self):
        try:
            name_latin = translit(self.name, 'ru', reversed=True)
        except Exception:
            name_latin = self.name

        base = re.sub(r'[^\w\s-]', '', name_latin.lower()).strip()
        base = re.sub(r'[\s_-]+', '-', base) or str(self.id)[:8]
        slug = base[:90]

        if Brand.all_objects.filter(slug=slug).exclude(id=self.id).exists():
            slug = f"{slug[:85]}-{str(self.id)[:8]}"

        return slug

    """Мягкое удаление."""

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
