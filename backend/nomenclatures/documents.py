from django_opensearch_dsl import Document, fields
from django_opensearch_dsl.registries import registry

from nomenclatures.models import Nomenclature


def _user_text(user) -> str:
    if not user:
        return ''
    return ' '.join(filter(None, [
        user.last_name,
        user.first_name,
        user.middle_name,
        user.email,
    ]))


def _counterparty_text(cp) -> str:
    if not cp:
        return ''
    return ' '.join(filter(None, [
        cp.first_name,
        cp.middle_name,
        cp.last_name,
        cp.keyword,
        cp.additional_name,
        cp.inn,
        cp.code1c,
    ]))


def _text_field():
    return fields.TextField(
        analyzer='autocomplete',
        search_analyzer='autocomplete_search',
    )


@registry.register_document
class NomenclatureDocument(Document):
    # ОСНОВНЫЕ ПОЛЯ
    name = _text_field()
    version = _text_field()
    code1c = _text_field()
    timezone = _text_field()
    contentType = _text_field()
    id_rasb = _text_field()

    # ДОП. ПОЛЯ
    brand_name = _text_field()
    legal_entity_text = _text_field()
    type_of_place = _text_field()
    content_type = _text_field()

    responsible_radio_text = _text_field()
    responsible_ad_text = _text_field()
    responsible_technic_text = _text_field()
    responsible_technic_on_address_text = _text_field()
    responsible_placement_marketing_text = _text_field()

    tenants_text = _text_field()

    class Index:
        name = 'nomenclatures'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'knn': True,
            'analysis': {
                'analyzer': {
                    'autocomplete': {
                        'tokenizer': 'autocomplete_tok',
                        'filter': ['lowercase'],
                    },
                    'autocomplete_search': {
                        'tokenizer': 'standard',
                        'filter': ['lowercase'],
                    },
                },
                'tokenizer': {
                    'autocomplete_tok': {
                        'type': 'ngram',
                        'min_gram': 2,
                        'max_gram': 20,
                        'token_chars': ['letter', 'digit'],
                    }
                }
            }
        }

    class Django:
        model = Nomenclature
        queryset_pagination = 1000
        fields = [
            'name^5',
            'code1c^4',
            'brand_name^3',
            'legal_entity_text^3',
            'type_of_place^2',
            'content_type^2',
            'tenants_text^3',
            'responsible_radio_text',
            'responsible_ad_text',
            'responsible_technic_text',
            'responsible_technic_on_address_text',
            'responsible_placement_marketing_text',
            'version',
        ]

    def get_queryset(self, **kwargs):
        return (
            super()
            .get_queryset(**kwargs)
            .select_related(
                'brand',
                'legalEntity',
                'typeOfPlace',
                'responsible_radio',
                'responsible_ad',
                'responsible_technic',
                'responsible_technic_on_address',
                'responsible_placement_marketing',
            )
            .prefetch_related(
                'nomenclature_tenants__tenant',
            )
        )

    def prepare_brand_name(self, instance) -> str:
        if not instance.brand:
            return ''
        return ' '.join(filter(None, [
            instance.brand.name,
            instance.brand.description,
            instance.brand.code1c,
        ]))

    def prepare_legal_entity_text(self, instance) -> str:
        return _counterparty_text(instance.legalEntity)

    def prepare_type_of_place(self, instance) -> str:
        if not instance.typeOfPlace:
            return ''
        return ' '.join(filter(None, [
            instance.typeOfPlace.name,
            instance.typeOfPlace.abbreviation,
            instance.typeOfPlace.tariff_single,
        ]))

    def prepare_content_type(self, instance) -> str:
        return instance.contentType or ''

    def prepare_responsible_radio_text(self, instance) -> str:
        return _user_text(instance.responsible_radio)

    def prepare_responsible_ad_text(self, instance) -> str:
        return _user_text(instance.responsible_ad)

    def prepare_responsible_technic_text(self, instance) -> str:
        return _user_text(instance.responsible_technic)

    def prepare_responsible_technic_on_address_text(self, instance) -> str:
        return _user_text(instance.responsible_technic_on_address)

    def prepare_responsible_placement_marketing_text(self, instance) -> str:
        return _user_text(instance.responsible_placement_marketing)

    def prepare_tenants_text(self, instance) -> str:
        parts = []
        for nt in instance.nomenclature_tenants.all():
            parts.append(_counterparty_text(nt.tenant))
        return ' '.join(filter(None, parts))
