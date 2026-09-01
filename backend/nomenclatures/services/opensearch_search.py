"""
Сервис поиска номенклатур через OpenSearch.

ОПТИМИЗАЦИЯ:
───────────────────────────────────────────────────────────────────────────────
1. Кеширование ID результатов вместо объекта Search
2. Ограничение количества результатов (SEARCH_LIMIT = 100)
3. Оптимизация полей поиска (убраны избыточные поля)
4. Обработка ошибок при выполнении запроса
5. Добавлено логирование с информацией о времени выполнения
"""

from opensearchpy import Q
import logging
import time
from hashlib import sha256
from django.core.cache import cache
from nomenclatures.documents import NomenclatureDocument

logger = logging.getLogger(__name__)


def _query_cache_key(query: str) -> str:
    """Returns a process-independent cache key component for a query."""
    return sha256(query.encode("utf-8")).hexdigest()


class NomenclatureOpenSearchService:
    """
    Сервис поиска номенклатур через OpenSearch.

    АТРИБУТЫ:
        CACHE_TIMEOUT (int): Время жизни кэша в секундах (5 минут)
        SEARCH_LIMIT (int): Максимальное количество результатов

    МЕТОДЫ:
        search(query, for_web, limit): Основной метод поиска
        clear_cache(query, for_web): Очистка кэша
    """

    CACHE_TIMEOUT = 60 * 5  # 5 минут
    SEARCH_LIMIT = 100  # Максимальное количество результатов

    @staticmethod
    def search(query: str, for_web: bool | None = True, limit: int = 50):
        """
        Поиск номенклатур через OpenSearch с кэшированием.

        Аргументы:
            query (str): Поисковый запрос
            for_web (bool, optional): Фильтр по for_web
            limit (int): Максимальное количество результатов

        Возвращает:
            Search: Объект поиска OpenSearch
        """
        start_time = time.time()
        query = (query or '').strip()

        # Ограничиваем количество результатов
        limit = min(limit, NomenclatureOpenSearchService.SEARCH_LIMIT)

        # Проверка кэша (кешируем ID результатов)
        cache_key = (
            f"opensearch_search_ids_{_query_cache_key(query)}_{for_web}_{limit}"
        )
        cached_ids = cache.get(cache_key)

        if cached_ids is not None:
            logger.info(f"Взято из кэша OpenSearch: '{query}' ({len(cached_ids)} ID)")
            # Возвращаем Search объект с ID из кэша
            s = NomenclatureDocument.search()
            if for_web is not None:
                s = s.filter('term', for_web=for_web)
            s = s.query('ids', values=cached_ids)
            return s

        # Создаем поисковый запрос
        s = NomenclatureDocument.search()

        if for_web is not None:
            s = s.filter('term', for_web=for_web)

        # Если запрос пустой - возвращаем последние записи
        if not query:
            try:
                result = s[:limit]
                # Кешируем ID результатов
                response = result.execute()
                ids_to_cache = [hit.meta.id for hit in response.hits]
                cache.set(cache_key, ids_to_cache, NomenclatureOpenSearchService.CACHE_TIMEOUT)
                logger.info(f"Закэшировано {len(ids_to_cache)} ID для пустого запроса")
                return result
            except Exception as e:
                logger.error(f"Ошибка при выполнении поиска (пустой запрос): {e}")
                return s[:limit]

        logger.info(f"Начало поиска OpenSearch: '{query}'")

        # Основные поля для поиска (высокий приоритет)
        primary_fields = [
            'name^10',
            'code1c^10',
            'id_rasb^8',
            'brand.name^8',
            'legalEntity.keyword^7',
            'tenants_data.tenant.keyword^6',
        ]

        # Вторичные поля (средний приоритет)
        secondary_fields = [
            'brand.code1c^6',
            'typeOfPlace.name^6',
            'typeOfPlace.abbreviation^5',
            'description^4',
            'legalEntity.first_name^4',
            'legalEntity.last_name^4',
            'tenants_data.tenant.first_name^4',
            'tenants_data.tenant.last_name^4',
        ]

        # Основной запрос (должен совпадать)
        must_query = Q(
            'bool',
            should=[
                Q(
                    'multi_match',
                    query=query,
                    type='best_fields',
                    fuzziness=0,
                    operator='or',
                    fields=primary_fields,
                ),
                Q('prefix', **{'name.raw': {'value': query.lower(), 'boost': 5}}),
            ],
            minimum_should_match=1,
        )

        # Дополнительные запросы (повышают релевантность)
        should_queries = [
            Q('term', **{'code1c.raw': query}),
            Q('term', **{'brand.code1c.raw': query}),
            Q('match_phrase', **{'name': {'query': query, 'boost': 3}}),
            Q('match_phrase', **{'brand.name': {'query': query, 'boost': 2}}),
            # Убираем search_text, если оно может отсутствовать
            # Q('match', search_text={'query': query, 'boost': 2}),
            Q(
                'multi_match',
                query=query,
                type='best_fields',
                fuzziness=1,
                operator='or',
                fields=primary_fields,
                boost=0.3,
            ),
            Q(
                'multi_match',
                query=query,
                type='best_fields',
                fuzziness=1,
                operator='or',
                fields=secondary_fields,
                boost=0.2,
            ),
        ]

        s = s.query(
            'bool',
            must=[must_query],
            should=should_queries,
        )

        # Ограничиваем количество результатов
        result = s.extra(size=limit)

        try:
            # Выполняем запрос для получения количества
            response = result.execute()
            total = response.hits.total['value']

            elapsed = time.time() - start_time
            logger.info(f"Поиск '{query}': найдено {total} результатов за {elapsed:.2f}с")

            # Кешируем ID результатов
            ids_to_cache = [hit.meta.id for hit in response.hits]
            cache.set(cache_key, ids_to_cache, NomenclatureOpenSearchService.CACHE_TIMEOUT)
            logger.info(f"Закэшировано {len(ids_to_cache)} ID для запроса '{query}'")

            return result

        except Exception as e:
            logger.error(f"Ошибка при выполнении поиска OpenSearch: {e}")
            # Возвращаем пустой результат при ошибке
            return s[:0]

    @staticmethod
    def clear_cache(
        query: str = None,
        for_web: bool | None = None,
        limit: int = 50,
    ):
        """
        Очищает кэш поиска OpenSearch.

        Аргументы:
            query (str, optional): Очищает кэш только для этого запроса
            for_web (bool, optional): Очищает кэш только для for_web
            limit (int): Лимит результатов, использованный при поиске
        """
        if query:
            cache_key = (
                f"opensearch_search_ids_{_query_cache_key(query)}_{for_web}_{limit}"
            )
            cache.delete(cache_key)
            logger.info(f"Очищен кэш OpenSearch для запроса: '{query}'")
        else:
            try:
                if hasattr(cache, 'delete_pattern'):
                    cache.delete_pattern("opensearch_search_ids_*")
                    logger.info("Очищен весь кэш OpenSearch")
                else:
                    logger.warning("Текущий cache backend не поддерживает delete_pattern")
            except AttributeError:
                logger.warning("Ошибка очистки кэша OpenSearch")

# from opensearchpy import Q
# import logging
# from nomenclatures.documents import NomenclatureDocument

# logger = logging.getLogger(__name__)


# class NomenclatureOpenSearchService:
#     @staticmethod
#     def search(query: str, for_web: bool | None = True, limit: int = 50):
#         s = NomenclatureDocument.search()

#         if for_web is not None:
#             s = s.filter('term', for_web=for_web)

#         query = (query or '').strip()

#         if not query:
#             return s[:limit]

#         logger.info(f"🔍 Начало поиска: '{query}'")

#         primary_fields = [
#             'name^10',
#             'code1c^10',
#             'id_rasb^6',
#             'brand.name^8',
#             'brand.code1c^8',
#             'typeOfPlace.name^8',
#             'typeOfPlace.abbreviation^8',
#             'legalEntity.keyword^8',
#             'tenants_data.tenant.keyword^7',
#             'tenants_data.brand.name^7',
#         ]

#         secondary_fields = [
#             'description^5',
#             'square^4',
#             'typeOfPlace.code1c^7',
#             'typeOfPlace.tariff^6',
#             'legalEntity.first_name^7',
#             'legalEntity.last_name^7',
#             'responsible_ad.first_name^4',
#             'responsible_ad.last_name^4',
#             'responsible_ad.full_name^5',
#             'tenants_data.tenant.first_name^6',
#             'tenants_data.tenant.last_name^6',
#             'tenants_data.brand.code1c^6',
#         ]

#         must_query = Q(
#             'bool',
#             should=[
#                 Q(
#                     'multi_match',
#                     query=query,
#                     type='best_fields',
#                     fuzziness=0,
#                     operator='or',
#                     fields=primary_fields,
#                 ),
#                 Q('prefix', **{'name.raw': {'value': query.lower(), 'boost': 5}}),
#             ],
#             minimum_should_match=1,
#         )

#         should_queries = [
#             Q('term', **{'code1c.raw': query}),
#             Q('term', **{'brand.code1c.raw': query}),
#             Q('term', **{'typeOfPlace.code1c.raw': query}),
#             Q('term', **{'legalEntity.keyword.raw': query}),
#             Q('term', **{'tenants_data.tenant.keyword.raw': query}),

#             Q('match_phrase', **{'name': {'query': query, 'boost': 3}}),
#             Q('match_phrase', **{'brand.name': {'query': query, 'boost': 2}}),

#             Q('match', search_text={'query': query, 'boost': 2}),

#             Q(
#                 'multi_match',
#                 query=query,
#                 type='best_fields',
#                 fuzziness=1,
#                 operator='or',
#                 fields=primary_fields,
#                 boost=0.3,
#             ),
#             Q(
#                 'multi_match',
#                 query=query,
#                 type='best_fields',
#                 fuzziness=1,
#                 operator='or',
#                 fields=secondary_fields,
#                 boost=0.2,
#             ),
#         ]

#         s = s.query(
#             'bool',
#             must=[must_query],
#             should=should_queries,
#         )

#         result = s.extra(size=limit)

#         response = result.execute()
#         total = response.hits.total['value']

#         logger.info(f"✅ Поиск '{query}': найдено {total} результатов")

#         return result
