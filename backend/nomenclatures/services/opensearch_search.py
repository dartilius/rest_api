from opensearchpy import Q

from nomenclatures.documents import NomenclatureDocument


class NomenclatureOpenSearchService:
    @staticmethod
    def search(query: str, is_active: bool | None = True, limit: int = 50):
        s = NomenclatureDocument.search()

        if is_active is not None:
            s = s.filter('term', is_active=is_active)

        query = (query or '').strip()

        if not query:
            return s[:limit]

        s = s.query(
            'bool',
            should=[
                # 1. Точные совпадения — самый высокий приоритет
                Q('term', **{'code1c.raw': query}),
                Q('term', **{'id': query}),
                Q('term', **{'brand.code1c.raw': query}),
                Q('term', **{'legalEntity.code1c.raw': query}),
                Q('term', **{'typeOfPlace.code1c.raw': query}),
                Q('term', **{'tenants_data.tenant.code1c.raw': query}),
                Q('term', **{'tenants_data.brand.code1c.raw': query}),

                # 2. Multi-match по основным полям
                Q(
                    'multi_match',
                    query=query,
                    type='best_fields',
                    fuzziness='AUTO',
                    fields=[
                        'name^10',
                        'code1c^10',
                        'article^8',
                        'description^5',
                        'version^5',
                        'square^3',
                        'possibility^3',
                        'id_rasb^6',

                        'brand.name^7',
                        'brand.code1c^7',

                        'legalEntity.name^8',
                        'legalEntity.short_name^7',
                        'legalEntity.full_name^7',
                        'legalEntity.code1c^7',
                        'legalEntity.inn^8',
                        'legalEntity.kpp^5',

                        'typeOfPlace.name^7',
                        'typeOfPlace.abbreviation^8',
                        'typeOfPlace.display_name^7',
                        'typeOfPlace.tariff^5',
                        'typeOfPlace.tariff_single^5',
                        'typeOfPlace.code1c^6',

                        'responsible_radio.email^4',
                        'responsible_radio.first_name^3',
                        'responsible_radio.last_name^3',
                        'responsible_radio.full_name^4',

                        'responsible_ad.email^4',
                        'responsible_ad.first_name^3',
                        'responsible_ad.last_name^3',
                        'responsible_ad.full_name^4',

                        'responsible_technic.email^4',
                        'responsible_technic.first_name^3',
                        'responsible_technic.last_name^3',
                        'responsible_technic.full_name^4',

                        'responsible_technic_on_address.email^4',
                        'responsible_technic_on_address.first_name^3',
                        'responsible_technic_on_address.last_name^3',
                        'responsible_technic_on_address.full_name^4',

                        'responsible_placement_marketing.email^4',
                        'responsible_placement_marketing.first_name^3',
                        'responsible_placement_marketing.last_name^3',
                        'responsible_placement_marketing.full_name^4',

                        'tenants_data.tenant.name^8',
                        'tenants_data.tenant.short_name^7',
                        'tenants_data.tenant.full_name^7',
                        'tenants_data.tenant.code1c^7',
                        'tenants_data.tenant.inn^8',
                        'tenants_data.tenant.kpp^5',

                        'tenants_data.brand.name^6',
                        'tenants_data.brand.code1c^6',
                        'tenants_data.floor^3',

                        'search_text^2',
                    ]
                ),

                # 3. Частичный wildcard — как страховка
                Q('wildcard', **{'name.raw': f'*{query.lower()}*'}) if len(query) >= 2 else Q('match_none'),
                Q('wildcard', **{'code1c.raw': f'*{query.lower()}*'}) if len(query) >= 2 else Q('match_none'),
            ],
            minimum_should_match=1
        )

        return s.extra(size=limit)