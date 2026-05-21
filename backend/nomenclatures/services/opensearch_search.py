from opensearchpy import Q
import logging
from nomenclatures.documents import NomenclatureDocument

logger = logging.getLogger(__name__)


class NomenclatureOpenSearchService:
    @staticmethod
    def search(query: str, is_active: bool | None = True, limit: int = 50):
        s = NomenclatureDocument.search()

        if is_active is not None:
            s = s.filter('term', is_active=is_active)

        query = (query or '').strip()

        if not query:
            return s[:limit]

        logger.info(f"🔍 Начало поиска: '{query}'")

        primary_fields = [
            'name^10',
            'code1c^10',
            'id_rasb^6',
            'brand.name^8',
            'brand.code1c^8',
            'typeOfPlace.name^8',
            'typeOfPlace.abbreviation^8',
            # 'legalEntity.description^7',
            'legalEntity.keyword^8',
            # 'tenants_data.tenant.description^7',
            'tenants_data.tenant.keyword^7',
            'tenants_data.brand.name^7',
        ]

        secondary_fields = [
            'description^5',
            'square^4',
            'typeOfPlace.code1c^7',
            'typeOfPlace.tariff^6',
            'legalEntity.first_name^7',
            'legalEntity.last_name^7',
            'responsible_ad.first_name^4',
            'responsible_ad.last_name^4',
            'responsible_ad.full_name^5',
            'tenants_data.tenant.first_name^6',
            'tenants_data.tenant.last_name^6',
            'tenants_data.brand.code1c^6',
        ]

        short_query = len(query) <= 4

        # must: только точное совпадение — определяет попадает ли объект в выдачу
        must_should = [
            Q(
                'multi_match',
                query=query,
                type='best_fields',
                fuzziness=0,
                operator='or',
                fields=primary_fields,
            ),
            Q('prefix', **{'name': {'value': query.lower(), 'boost': 5}}),
        ]

        # search_text через edge ngram — только для длинных запросов (5+ символов)
        # для коротких даёт слишком много шума
        if not short_query:
            must_should.append(
                Q('match', search_text={'query': query, 'boost': 3})
            )

        must_query = Q(
            'bool',
            should=must_should,
            minimum_should_match=1,
        )

        # should: поднимает score для более релевантных результатов,
        # но не добавляет лишние объекты (fuzziness только здесь)
        should_queries = [
            # точные совпадения по кодам — максимальный буст
            Q('term', **{'code1c.raw': query}),
            Q('term', **{'brand.code1c.raw': query}),
            Q('term', **{'typeOfPlace.code1c.raw': query}),
            Q('term', **{'legalEntity.keyword.raw': query}),
            Q('term', **{'tenants_data.tenant.keyword.raw': query}),

            # фразовые совпадения
            Q('match_phrase', **{'name': {'query': query, 'boost': 3}}),
            Q('match_phrase', **{'brand.name': {'query': query, 'boost': 2}}),

            # fuzziness только в should — поднимает score для похожих,
            # но не добавляет нерелевантные объекты в выдачу
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
            minimum_should_match=0,
        )

        result = s.extra(size=limit)
        response = result.execute()
        total = response.hits.total['value']
        logger.info(f"✅ Поиск '{query}': найдено {total} результатов")

        return result