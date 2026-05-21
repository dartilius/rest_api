# from opensearchpy import Q

# from nomenclatures.documents import NomenclatureDocument


# class NomenclatureOpenSearchService:
#     @staticmethod
#     def search(query: str, is_active: bool | None = True, limit: int = 50):
#         s = NomenclatureDocument.search()

#         if is_active is not None:
#             s = s.filter('term', is_active=is_active)

#         query = (query or '').strip()

#         if not query:
#             return s[:limit]

#         should_queries = [
#             # 1. Точные совпадения
#             Q('term', **{'code1c.raw': query}),
#             Q('term', **{'brand.code1c.raw': query}),
#             Q('term', **{'typeOfPlace.code1c.raw': query}),
#             Q('term', **{'legalEntity.description.raw': query}),
#             Q('term', **{'legalEntity.keyword.raw': query}),
#             Q('term', **{'tenants_data.tenant.description.raw': query}),
#             Q('term', **{'tenants_data.brand.code1c.raw': query}),
#         ]

#         # 2. Multi-match по основным полям (только существующие)
#         should_queries.append(
#             Q(
#                 'multi_match',
#                 query=query,
#                 type='best_fields',
#                 fuzziness='AUTO',
#                 fields=[
#                     'name^10',
#                     'code1c^10',
#                     'description^5',
#                     'id_rasb^6',

#                     'brand.name^7',
#                     'brand.code1c^7',

#                     'legalEntity.first_name^8',    # ← существующее поле
#                     'legalEntity.middle_name^7',   # ← существующее поле
#                     'legalEntity.last_name^7',     # ← существующее поле
#                     'legalEntity.description^7',   # ← существующее поле (хранит code1c)
#                     'legalEntity.keyword^8',       # ← существующее поле (хранит inn)
#                     'legalEntity.additional_name^5',  # ← существующее поле (хранит kpp)

#                     'typeOfPlace.name^7',
#                     'typeOfPlace.abbreviation^8',
#                     'typeOfPlace.display_name^7',
#                     'typeOfPlace.tariff^5',
#                     'typeOfPlace.tariff_single^5',
#                     'typeOfPlace.code1c^6',

#                     'responsible_radio.email^4',
#                     'responsible_radio.first_name^3',
#                     'responsible_radio.last_name^3',
#                     'responsible_radio.full_name^4',

#                     'responsible_ad.email^4',
#                     'responsible_ad.first_name^3',
#                     'responsible_ad.last_name^3',
#                     'responsible_ad.full_name^4',

#                     'responsible_technic.email^4',
#                     'responsible_technic.first_name^3',
#                     'responsible_technic.last_name^3',
#                     'responsible_technic.full_name^4',

#                     'responsible_technic_on_address.email^4',
#                     'responsible_technic_on_address.first_name^3',
#                     'responsible_technic_on_address.last_name^3',
#                     'responsible_technic_on_address.full_name^4',

#                     'responsible_placement_marketing.email^4',
#                     'responsible_placement_marketing.first_name^3',
#                     'responsible_placement_marketing.last_name^3',
#                     'responsible_placement_marketing.full_name^4',

#                     'tenants_data.tenant.first_name^8',   # ← существующее поле
#                     'tenants_data.tenant.middle_name^7',  # ← существующее поле
#                     'tenants_data.tenant.last_name^7',    # ← существующее поле
#                     'tenants_data.tenant.description^7',  # ← существующее поле
#                     'tenants_data.tenant.keyword^8',      # ← существующее поле
#                     'tenants_data.tenant.additional_name^5',  # ← существующее поле

#                     'tenants_data.brand.name^6',
#                     'tenants_data.brand.code1c^6',
#                     'tenants_data.floor^3',

#                     'search_text^2',
#                 ]
#             )
#         )

#         # 3. Частичный wildcard — как страховка
#         if len(query) >= 2:
#             should_queries.extend([
#                 Q('wildcard', **{'name.raw': f'*{query}*'}),
#                 Q('wildcard', **{'code1c.raw': f'*{query}*'}),
#             ])
#         else:
#             should_queries.extend([Q('match_none'), Q('match_none')])

#         s = s.query('bool', should=should_queries, minimum_should_match=1)

#         return s.extra(size=limit)

# from opensearchpy import Q
# from nomenclatures.documents import NomenclatureDocument
# import logging

# logger = logging.getLogger(__name__)

# class NomenclatureOpenSearchService:
#     @staticmethod
#     def search(query: str, is_active: bool | None = True, limit: int = 50):
#         s = NomenclatureDocument.search()

#         if is_active is not None:
#             s = s.filter('term', is_active=is_active)

#         query = (query or '').strip()

#         if not query:
#             logger.info("Пустой поисковый запрос")
#             return s[:limit]

#         logger.info(f"🔍 Начало поиска: '{query}'")

#         # MUST queries (обязательные условия для релевантности)
#         must_queries = []

#         # 1. Поиск по основным полям (точные и приблизительные совпадения)
#         must_queries.append(
#             Q(
#                 'multi_match',
#                 query=query,
#                 type='best_fields',
#                 fuzziness='AUTO',
#                 operator='or',
#                 fields=[
#                     'name^10',              # название номенклатуры
#                     'code1c^10',            # код 1С номенклатуры
#                     'id_rasb^6',            # код РАСБ
#                     'description^5',        # описание

#                     'brand.name^7',         # название бренда
#                     'brand.code1c^7',       # код 1С бренда

#                     'typeOfPlace.name^7',   # тип места размещения
#                     'typeOfPlace.abbreviation^8',
#                     'typeOfPlace.code1c^6',

#                     'legalEntity.tenant.first_name^4',
#                     'legalEntity.tenant.last_name^4',
#                     'legalEntity.brand.name^4',
#                     'legalEntity.description^7',
#                     'legalEntity.keyword^8',

#                     # 🔴 Ответственные лица
#                     'responsible_ad.first_name^4',
#                     'responsible_ad.last_name^4',
#                     'responsible_ad.full_name^5',

#                     # 🔴 Арендаторы
#                     'tenants_data.tenant.first_name^4',
#                     'tenants_data.tenant.last_name^4',
#                     'tenants_data.tenant.description^6',
#                     'tenants_data.tenant.keyword^6',
#                     'tenants_data.brand.name^4',        # бренд арендатора
#                 ]
#             )
#         )

#         # SHOULD queries (дополнительные совпадения для бустинга)
#         should_queries = []

#         # 2. Точные совпадения (высокий приоритет)
#         should_queries.extend([
#             Q('term', **{'code1c.raw': query}),
#             Q('term', **{'brand.code1c.raw': query}),
#             Q('term', **{'typeOfPlace.code1c.raw': query}),
#             Q('term', **{'legalEntity.keyword.raw': query}),
#             Q('term', **{'tenants_data.tenant.keyword.raw': query}),  # ИНН арендатора
#         ])

#         # 3. Фраза (для более точного поиска)
#         should_queries.append(
#             Q('match_phrase', name={'query': query, 'boost': 2})
#         )

#         # Применяем логику: MUST основной поиск + SHOULD для бустинга релевантности
#         s = s.query(
#             'bool',
#             must=must_queries,
#             should=should_queries,
#             minimum_should_match=0,
#             boost_mode='multiply'
#         )
#         logger.debug(f"OpenSearch Query: {s.to_dict()}")

#         result = s.extra(size=limit)

#         # 🔴 ЛОГИРОВАНИЕ РЕЗУЛЬТАТА
#         response = result.execute()
#         logger.info(f"✅ Поиск '{query}': найдено {response.hits.total['value']} результатов")

#         for i, hit in enumerate(response[:5], 1):
#             logger.debug(f"  {i}. {hit.meta.id} - Score: {hit.meta.score:.2f}")


#         return result


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
            'legalEntity.description^7',
            'legalEntity.keyword^8',
            'tenants_data.tenant.description^7',
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

        # must: достаточно совпасть хотя бы в одном из вариантов
        must_query = Q(
            'bool',
            should=[
                # 1. Полнотекстовый поиск с fuzziness (опечатки)
                Q(
                    'multi_match',
                    query=query,
                    type='best_fields',
                    fuzziness=1,
                    operator='or',
                    fields=primary_fields,
                ),
                # 2. Частичное вхождение через search_text (edge ngram)
                Q('match', search_text={'query': query, 'boost': 3}),
                # 3. Prefix по name.raw для коротких запросов (< 20 символов)
                Q('prefix', **{'name': {'value': query.lower(), 'boost': 5}}),
                # 4. Wildcard — крайний случай для середины строки
                Q('wildcard', **{'name': {'value': f'*{query.lower()}*', 'boost': 1}}),
            ],
            minimum_should_match=1,
        )

        should_queries = [
            Q('term', **{'code1c.raw': query}),
            Q('term', **{'brand.code1c.raw': query}),
            Q('term', **{'typeOfPlace.code1c.raw': query}),
            Q('term', **{'legalEntity.keyword.raw': query}),
            Q('term', **{'tenants_data.tenant.keyword.raw': query}),
            Q('match_phrase', **{'name': {'query': query, 'boost': 3}}),
            Q('match_phrase', **{'brand.name': {'query': query, 'boost': 2}}),
            Q(
                'multi_match',
                query=query,
                type='best_fields',
                fuzziness='AUTO',
                operator='or',
                fields=secondary_fields,
                boost=0.5,
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