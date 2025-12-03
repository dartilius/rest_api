from django.db import models
from rest_framework.filters import SearchFilter

EXCLUDED_FIELDS = {
    """
    Поля, по которым не нужно искать
    Чтобы добавить поля для исколючения, в views добавить переменную search_excluded_fields.
    Пример: search_excluded_fields = ["brand__description"]
    """
    "settings", "hw_info", "version", "timezone",
    "description",
    # "traffic", "floor_space",
    "keys_validator", "contentType", "pricePerMonth"
}


class UniversalSearchFilter(SearchFilter):
    """
    Универсальный фильтр для поиска по строковым полям модели и связанных моделей.
    Автоматически определяет search_fields и кэширует результат.
    """

    # Простой in-memory кэш (на уровне процесса)
    _search_fields_cache = {}

    def get_search_fields(self, view, request):
        """
        Возвращает список полей для поиска. Берёт из кэша, если уже вычислено.
        """
        model = view.queryset.model
        cache_key = model._meta.label_lower  # например: "nomenclature.nomenclature"

        # Проверяем кэш
        if cache_key not in self._search_fields_cache:
            max_depth = getattr(view, "search_depth", 2)
            excluded = set(EXCLUDED_FIELDS) | set(getattr(view, "search_excluded_fields", []))
            fields = self._collect_search_fields(model, excluded=excluded, max_depth=max_depth)
            self._search_fields_cache[cache_key] = fields

        return self._search_fields_cache[cache_key]

    def _collect_search_fields(self, model, prefix="", depth=0, max_depth=2, excluded=None):
        """
        Рекурсивно собирает строковые поля и связи до max_depth уровней.
        """
        search_fields = []
        if depth > max_depth:
            return search_fields

        for field in model._meta.get_fields():
            # Пропускаем технические, служебные и обратные связи
            if (
                    field.name in excluded
                    or (field.is_relation and field.auto_created and not field.concrete)
            ):
                continue

            field_path = f"{prefix}__{field.name}" if prefix else field.name

            # Строковые поля
            if isinstance(field, (models.CharField, models.TextField)):
                search_fields.append(field_path)

            # Связанные модели
            elif isinstance(field, (models.ForeignKey, models.OneToOneField, models.ManyToManyField)):
                related_model = field.related_model
                search_fields.extend(
                    self._collect_search_fields(
                        related_model,
                        prefix=field_path,
                        depth=depth + 1,
                        max_depth=max_depth,
                        excluded=excluded,
                    )
                )

        return search_fields
