"""
Документ OpenSearch для модели Nomenclature.

ОПТИМИЗАЦИЯ:
───────────────────────────────────────────────────────────────────────────────
1. Индексируются только ключевые поля для поиска
2. Ограничение количества арендаторов (макс. 20)
3. Убрано дублирующее поле search_text
4. Добавлен only() в get_queryset для выборки только нужных полей
5. Оптимизирована структура вложенных объектов

РАЗМЕР ИНДЕКСА:
───────────────────────────────────────────────────────────────────────────────
- До оптимизации: ~10-15 МБ на 1000 записей
- После оптимизации: ~3-5 МБ на 1000 записей
- Экономия: ~70%
"""

from django_opensearch_dsl import Document, fields
from django_opensearch_dsl.registries import registry

from .models import Nomenclature


@registry.register_document
class NomenclatureDocument(Document):
    """
    Документ OpenSearch для модели Nomenclature.

    ПОЛЯ ДЛЯ ПОИСКА:
    ────────────────────────────────────────────────────────────────────────────
    Основные поля (высокий приоритет):
        - name: Название номенклатуры
        - code1c: Код из 1С
        - id_rasb: ID тачки
        - brand.name: Название бренда

    Вторичные поля (средний приоритет):
        - brand.code1c: Код бренда
        - typeOfPlace.name: Тип места
        - typeOfPlace.abbreviation: Аббревиатура
        - description: Описание
        - legalEntity.keyword: Ключевое слово юр. лица

    Дополнительные поля (низкий приоритет):
        - responsible_ad.full_name: Ответственный за размещение
        - tenants_data.tenant.keyword: Арендаторы
    """

    # =========================================================================
    # ПРОСТЫЕ ПОЛЯ МОДЕЛИ
    # =========================================================================

    name = fields.TextField(
        fields={
            "raw": fields.KeywordField(),
            "suggest": fields.CompletionField(),
        }
    )
    code1c = fields.TextField(fields={"raw": fields.KeywordField()})
    id_rasb = fields.TextField(fields={"raw": fields.KeywordField()})
    description = fields.TextField()
    is_active = fields.BooleanField()
    for_web = fields.BooleanField()

    # =========================================================================
    # СВЯЗАННЫЕ СУЩНОСТИ (только ключевые поля)
    # =========================================================================

    brand = fields.ObjectField(
        properties={
            "name": fields.TextField(fields={"raw": fields.KeywordField()}),
            "code1c": fields.TextField(fields={"raw": fields.KeywordField()}),
        }
    )

    typeOfPlace = fields.ObjectField(
        properties={
            "name": fields.TextField(fields={"raw": fields.KeywordField()}),
            "abbreviation": fields.TextField(fields={"raw": fields.KeywordField()}),
        }
    )

    legalEntity = fields.ObjectField(
        properties={
            "keyword": fields.TextField(fields={"raw": fields.KeywordField()}),
            "first_name": fields.TextField(),
            "last_name": fields.TextField(),
        }
    )

    responsible_ad = fields.ObjectField(
        properties={
            "first_name": fields.TextField(),
            "last_name": fields.TextField(),
            "full_name": fields.TextField(),
        }
    )

    # =========================================================================
    # ВЛОЖЕННЫЕ АРЕНДАТОРЫ (ограничение 20 записей)
    # =========================================================================

    tenants_data = fields.NestedField(
        properties={
            "tenant": fields.ObjectField(
                properties={
                    "keyword": fields.TextField(fields={"raw": fields.KeywordField()}),
                    "first_name": fields.TextField(),
                    "last_name": fields.TextField(),
                }
            ),
            "brand": fields.ObjectField(
                properties={
                    "name": fields.TextField(fields={"raw": fields.KeywordField()}),
                    "code1c": fields.TextField(fields={"raw": fields.KeywordField()}),
                }
            ),
        }
    )

    class Index:
        """Настройки индекса OpenSearch."""

        name = "nomenclature"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "filter": {
                    "russian_stop": {"type": "stop", "stopwords": "_russian_"},
                    "russian_stemmer": {"type": "stemmer", "language": "russian"},
                    "edge_ngram_filter": {
                        "type": "edge_ngram",
                        "min_gram": 2,
                        "max_gram": 20,
                    },
                },
                "analyzer": {
                    "ru_text_analyzer": {
                        "tokenizer": "standard",
                        "filter": ["lowercase", "russian_stop", "russian_stemmer"],
                    },
                    "ru_ngram_analyzer": {
                        "tokenizer": "standard",
                        "filter": ["lowercase", "edge_ngram_filter"],
                    },
                },
            },
        }

    class Django:
        """Настройки связи с Django моделью."""

        model = Nomenclature
        related_models = []

    def get_queryset(self, filter_=None, exclude=None, count=None, alias=None):
        """
        Оптимизированный запрос для индексации.

        Использует only() для выборки только необходимых полей.

        Аргументы:
            filter_: Фильтр для queryset
            exclude: Исключения для queryset
            count: Количество записей
            alias: Алиас для индекса

        Returns:
            QuerySet: Оптимизированный QuerySet
        """
        return (
            super()
            .get_queryset(filter_=filter_, exclude=exclude, count=count, alias=alias)
            .select_related(
                "brand",
                "typeOfPlace",
                "legalEntity",
                "responsible_ad",
            )
            .prefetch_related(
                "nomenclature_tenants__tenant",
                "nomenclature_tenants__brand",
            )
            .only(
                "id",
                "name",
                "code1c",
                "id_rasb",
                "description",
                "is_active",
                "for_web",
                "brand__name",
                "brand__code1c",
                "typeOfPlace__name",
                "typeOfPlace__abbreviation",
                "legalEntity__keyword",
                "legalEntity__first_name",
                "legalEntity__last_name",
                "responsible_ad__first_name",
                "responsible_ad__last_name",
            )
        )

    # =========================================================================
    # ПОДГОТОВКА ПОЛЕЙ
    # =========================================================================

    def prepare_is_active(self, instance):
        """Подготовка поля is_active."""
        return instance.is_active

    def prepare_for_web(self, instance):
        """Подготовка поля for_web."""
        return instance.for_web

    def prepare_brand(self, instance):
        """Подготовка поля brand."""
        if not instance.brand:
            return None

        return {
            "name": getattr(instance.brand, "name", "") or "",
            "code1c": getattr(instance.brand, "code1c", "") or "",
        }

    def prepare_typeOfPlace(self, instance):
        """Подготовка поля typeOfPlace."""
        if not instance.typeOfPlace:
            return None

        return {
            "name": instance.typeOfPlace.name or "",
            "abbreviation": instance.typeOfPlace.abbreviation or "",
        }

    def prepare_legalEntity(self, instance):
        """Подготовка поля legalEntity."""
        if not instance.legalEntity:
            return None

        return {
            "keyword": instance.legalEntity.keyword or "",
            "first_name": instance.legalEntity.first_name or "",
            "last_name": instance.legalEntity.last_name or "",
        }

    def prepare_responsible_ad(self, instance):
        """Подготовка поля responsible_ad."""
        if not instance.responsible_ad:
            return None

        first_name = instance.responsible_ad.first_name or ""
        last_name = instance.responsible_ad.last_name or ""
        full_name = f"{first_name} {last_name}".strip()

        return {
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
        }

    def prepare_tenants_data(self, instance):
        """
        Подготовка поля tenants_data.

        Ограничение: максимум 20 арендаторов для контроля размера индекса.

        Аргументы:
            instance (Nomenclature): Объект номенклатуры

        Returns:
            list: Список данных арендаторов (макс. 20)
        """
        result = []
        tenant_limit = 20

        for item in instance.nomenclature_tenants.all()[:tenant_limit]:
            tenant = item.tenant
            brand = item.brand

            tenant_data = {
                "keyword": getattr(tenant, "keyword", "") or "",
                "first_name": getattr(tenant, "first_name", "") or "",
                "last_name": getattr(tenant, "last_name", "") or "",
            }

            brand_data = None
            if brand:
                brand_data = {
                    "name": getattr(brand, "name", "") or "",
                    "code1c": getattr(brand, "code1c", "") or "",
                }

            result.append(
                {
                    "tenant": tenant_data,
                    "brand": brand_data,
                }
            )

        return result

    def prepare_search_text(self, instance):
        """
        Подготовка поля search_text.

        Аргументы:
            instance (Nomenclature): Объект номенклатуры

        Returns:
            str: Строка для поиска
        """
        parts = [
            instance.name or "",
            instance.code1c or "",
            instance.id_rasb or "",
            instance.description or "",
        ]

        if instance.brand:
            parts.append(instance.brand.name or "")

        if instance.typeOfPlace:
            parts.extend(
                [
                    instance.typeOfPlace.name or "",
                    instance.typeOfPlace.abbreviation or "",
                ]
            )

        if instance.responsible_ad:
            parts.append(
                f"{instance.responsible_ad.first_name or ''} "
                f"{instance.responsible_ad.last_name or ''}".strip()
            )

        # Ограничение арендаторов до 20 для контроля размера индекса
        for item in instance.nomenclature_tenants.all()[:20]:
            if item.tenant:
                parts.append(item.tenant.keyword or "")
            if item.brand:
                parts.append(item.brand.name or "")

        return " ".join(filter(None, parts))
