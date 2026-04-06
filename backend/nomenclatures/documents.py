from django_opensearch_dsl import Document, fields
from django_opensearch_dsl.registries import registry
from nomenclatures.models import Nomenclature, NomenclatureTenant


@registry.register_document
class NomenclatureDocument(Document):

    # Связанные поля (денормализуем в индекс)
    brand_name = fields.TextField(attr='brand.name')
    legal_entity_name = fields.TextField()
    legal_entity_keyword = fields.KeywordField()
    type_of_place = fields.TextField()
    tenants_text = fields.TextField()

    responsible_radio_name = fields.TextField()
    responsible_ad_name = fields.TextField()
    responsible_technic_name = fields.TextField()

    class Index:
        name = 'nomenclatures'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'analysis': {
                'analyzer': {
                    # Анализатор с поддержкой частичного вхождения
                    'autocomplete': {
                        'tokenizer': 'autocomplete_tokenizer',
                        'filter': ['lowercase'],
                    },
                    'autocomplete_search': {
                        'tokenizer': 'lowercase',
                    },
                },
                'tokenizer': {
                    'autocomplete_tokenizer': {
                        'type': 'edge_ngram',
                        'min_gram': 2,
                        'max_gram': 20,
                        'token_chars': ['letter', 'digit'],
                    }
                }
            }
        }

    class Django:
        model = Nomenclature
        fields = ['name', 'version', 'code1c', 'timezone']
        queryset_pagination = 500

    def get_queryset(self, **kwargs):
        return (
            super()
            .get_queryset(**kwargs)  # передаём все аргументы в родительский метод
            .select_related(
                'brand', 'legalEntity', 'typeOfPlace',
                'responsible_radio', 'responsible_ad', 'responsible_technic',
            )
            .prefetch_related('tenants__tenant')
        )

    def prepare_legal_entity_name(self, instance):
        if instance.legalEntity:
            parts = filter(None, [
                instance.legalEntity.first_name,
                instance.legalEntity.last_name,
                instance.legalEntity.additional_name,
            ])
            return ' '.join(parts)
        return ''

    def prepare_legal_entity_keyword(self, instance):
        return instance.legalEntity.keyword if instance.legalEntity else ''

    def prepare_type_of_place(self, instance):
        return instance.typeOfPlace.name if instance.typeOfPlace else ''

    def prepare_tenants_text(self, instance):
        parts = []
        for t in instance.tenants.all():
            tenant = t.tenant
            parts.append(' '.join(filter(None, [
                tenant.first_name,
                tenant.last_name,
                tenant.additional_name,
                tenant.keyword,
                t.floor,
            ])))
        return ' '.join(parts)

    def prepare_responsible_radio_name(self, instance):
        r = instance.responsible_radio
        return f'{r.first_name} {r.last_name}' if r else ''

    def prepare_responsible_ad_name(self, instance):
        r = instance.responsible_ad
        return f'{r.first_name} {r.last_name}' if r else ''

    def prepare_responsible_technic_name(self, instance):
        r = instance.responsible_technic
        return f'{r.first_name} {r.last_name}' if r else ''