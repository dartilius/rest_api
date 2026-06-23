"""
Сервис поиска номенклатур через Django ORM.

ОПТИМИЗАЦИЯ:
───────────────────────────────────────────────────────────────────────────────
1. Использование search_vector для полнотекстового поиска
2. Кэширование результатов на 5 минут
3. Кэширование пустых запросов
4. Ограничение количества результатов
5. Обработка ошибок при очистке кэша
"""

import logging
from django.db.models import Q
from nomenclatures.models import Nomenclature
from django.core.cache import cache

logger = logging.getLogger(__name__)


class NomenclatureSearchService:
    """
    Сервис поиска номенклатур через Django ORM.

    АТРИБУТЫ:
        CACHE_TIMEOUT (int): Время жизни кэша в секундах (5 минут)
        SEARCH_LIMIT (int): Максимальное количество результатов
    """

    CACHE_TIMEOUT = 60 * 5
    SEARCH_LIMIT = 100

    @staticmethod
    def search(query: str, for_web: bool = True, limit: int = 50, use_cache: bool = True):
        """
        Основной метод поиска номенклатур.

        Аргументы:
            query (str): Поисковый запрос
            for_web (bool): Фильтровать только для веба
            limit (int): Максимальное количество результатов
            use_cache (bool): Использовать кэширование

        Returns:
            QuerySet: QuerySet с результатами поиска
        """
        query = (query or '').strip()

        if not query:
            cache_key = f"nomenclature_search_empty_{for_web}_{limit}"
            cached_ids = cache.get(cache_key)

            if cached_ids is not None:
                qs = Nomenclature.objects.filter(id__in=cached_ids)
                return NomenclatureSearchService._optimize_queryset(qs)

            qs = Nomenclature.objects.filter(for_web=for_web) if for_web else Nomenclature.objects.all()
            qs = NomenclatureSearchService._optimize_queryset(qs)[
                 :min(limit, NomenclatureSearchService.SEARCH_LIMIT)]

            ids_to_cache = list(qs.values_list('id', flat=True))
            cache.set(cache_key, ids_to_cache, NomenclatureSearchService.CACHE_TIMEOUT)
            return qs

        if use_cache:
            cache_key = f"nomenclature_search_ids_{hash(query)}_{for_web}_{limit}"
            cached_ids = cache.get(cache_key)

            if cached_ids is not None:
                logger.info(f"Взято из кэша: {len(cached_ids)} результатов для '{query}'")
                queryset = Nomenclature.objects.filter(id__in=cached_ids)
                return NomenclatureSearchService._optimize_queryset(queryset)[
                       :min(limit, NomenclatureSearchService.SEARCH_LIMIT)]

        logger.info(f"Поиск номенклатур: '{query}'")

        queryset = Nomenclature.objects.filter(for_web=for_web)

        conditions = Q(search_vector__icontains=query.lower())
        conditions |= Q(code1c__iexact=query)
        conditions |= Q(id_rasb__iexact=query)
        conditions |= Q(name__istartswith=query)
        conditions |= Q(name__icontains=query)

        queryset = queryset.filter(conditions).distinct()
        queryset = NomenclatureSearchService._optimize_queryset(queryset)

        if use_cache:
            ids_to_cache = list(queryset.values_list('id', flat=True)[
                                :min(limit, NomenclatureSearchService.SEARCH_LIMIT)])
            cache.set(cache_key, ids_to_cache, NomenclatureSearchService.CACHE_TIMEOUT)
            logger.info(f"Закэшировано {len(ids_to_cache)} ID")

        return queryset[:min(limit, NomenclatureSearchService.SEARCH_LIMIT)]

    @staticmethod
    def _optimize_queryset(queryset):
        """Добавляет оптимизации к queryset."""
        return queryset.select_related(
            'brand',
            'typeOfPlace',
        ).prefetch_related(
            'nomenclature_tenants__tenant',
            'nomenclature_tenants__brand',
        ).only(
            'id', 'name', 'code1c', 'description',
            'brand__name', 'brand__id',
            'typeOfPlace__name', 'typeOfPlace__id'
        )

    @staticmethod
    def clear_cache(query: str = None, for_web: bool = True):
        """
        Очищает кэш поиска.

        Аргументы:
            query (str, optional): Очищает кэш только для этого запроса
            for_web (bool): Очищает кэш только для for_web
        """
        if query:
            cache_key = f"nomenclature_search_ids_{hash(query)}_{for_web}"
            cache.delete(cache_key)
            cache.delete(f"nomenclature_search_empty_{for_web}")
            logger.info(f"Очищен кэш для запроса: '{query}'")
        else:
            try:
                if hasattr(cache, 'delete_pattern'):
                    cache.delete_pattern("nomenclature_search_ids_*")
                    cache.delete_pattern("nomenclature_search_empty_*")
                    logger.info("Очищен весь кэш поиска")
                else:
                    logger.warning("Текущий cache backend не поддерживает delete_pattern")
            except AttributeError:
                logger.warning("Ошибка очистки кэша")

# # nomenclatures/services/search.py

# import logging
# from django.db.models import Q
# from nomenclatures.models import Nomenclature
# from django.core.cache import cache

# logger = logging.getLogger(__name__)


# class NomenclatureSearchService:
#     """Сервис поиска номенклатур через Django ORM."""

#     CACHE_TIMEOUT = 60 * 5  # 5 минут

#     @staticmethod
#     def search(query: str, for_web: bool = True, limit: int = 50, use_cache: bool = True):
#         """
#         Основной метод поиска.

#         Args:
#             query: Поисковый запрос
#             for_web: Фильтровать только для веба
#             limit: Максимальное количество результатов
#             use_cache: Использовать кэширование

#         Returns:
#             QuerySet с результатами поиска
#         """
#         query = (query or '').strip()

#         if not query:
#             return Nomenclature.objects.filter(for_web=for_web)[:limit] if for_web else Nomenclature.objects.all()[
#                 :limit]

#         # Проверяем кэш
#         if use_cache:
#             cache_key = f"nomenclature_search_ids_{hash(query)}_{for_web}_{limit}"
#             cached_ids = cache.get(cache_key)

#             if cached_ids is not None:
#                 logger.info(f"📦 Взято из кэша: {len(cached_ids)} результатов для '{query}'")
#                 # Восстанавливаем queryset из закэшированных ID
#                 queryset = Nomenclature.objects.filter(id__in=cached_ids)
#                 return NomenclatureSearchService._optimize_queryset(queryset)[:limit]

#         logger.info(f"🔍 Поиск номенклатур: '{query}'")

#         # Базовый queryset
#         queryset = Nomenclature.objects.all()
#         if for_web:
#             queryset = queryset.filter(for_web=True)

#         # Строим условия поиска
#         conditions = Q()

#         # 1. Точные совпадения по кодам
#         conditions |= Q(code1c__iexact=query)
#         conditions |= Q(id_rasb__iexact=query)

#         # 2. Поиск по подстроке в search_vector
#         if for_web:
#             conditions |= Q(search_vector__icontains=query.lower())
#         else:
#             conditions |= Q(
#                 Q(for_web=True) & Q(search_vector__icontains=query.lower())
#             )

#         # 3. Поиск по началу имени (приоритетнее)
#         conditions |= Q(name__istartswith=query)

#         queryset = queryset.filter(conditions)

#         # Оптимизация запросов
#         queryset = NomenclatureSearchService._optimize_queryset(queryset)

#         result_count = queryset.count()
#         logger.info(f"✅ Найдено: {result_count} результатов")

#         # Кэшируем ID результатов
#         if use_cache:
#             ids_to_cache = list(queryset.values_list('id', flat=True)[:limit])
#             cache.set(cache_key, ids_to_cache, NomenclatureSearchService.CACHE_TIMEOUT)
#             logger.info(f"💾 Закэшировано {len(ids_to_cache)} ID")

#         return queryset[:limit]

#     @staticmethod
#     def _optimize_queryset(queryset):
#         """Добавляет оптимизации к queryset."""
#         return queryset.select_related(
#             'brand',
#             'typeOfPlace',
#             'responsible_radio',
#             'responsible_ad',
#             'responsible_technic',
#             'responsible_technic_on_address',
#             'responsible_placement_marketing',
#         ).prefetch_related(
#             'nomenclature_tenants__tenant',
#             'nomenclature_tenants__brand',
#         )

#     @staticmethod
#     def clear_cache(query: str = None, for_web: bool = True):
#         """
#         Очищает кэш поиска.

#         Args:
#             query: Если указан, очищает кэш только для этого запроса.
#                   Если None, очищает весь кэш поиска.
#         """
#         if query:
#             cache_key = f"nomenclature_search_ids_{hash(query)}_{for_web}"
#             cache.delete(cache_key)
#             logger.info(f"🗑 Очищен кэш для запроса: '{query}'")
#         else:
#             # Очищаем все ключи, связанные с поиском
#             # Примечание: это работает только с Redis cache
#             try:
#                 cache.delete_pattern("nomenclature_search_ids_*")
#                 logger.info("🗑 Очищен весь кэш поиска")
#             except AttributeError:
#                 logger.warning("Текущий cache backend не поддерживает delete_pattern")