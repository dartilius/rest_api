from django_opensearch_dsl import Document, fields
from django_opensearch_dsl.registries import registry

from .models import Nomenclature


@registry.register_document
class NomenclatureDocument(Document):
    # --- Простые поля модели ---
    name = fields.TextField(
        fields={
            'raw': fields.KeywordField(),
            'suggest': fields.CompletionField(),
        }
    )
    code1c = fields.TextField(fields={'raw': fields.KeywordField()})
    description = fields.TextField()
    square = fields.TextField()
    is_active = fields.BooleanField()
    id_rasb = fields.TextField(fields={'raw': fields.KeywordField()})

    # --- Связанные сущности ---
    brand = fields.ObjectField(properties={
        'name': fields.TextField(fields={'raw': fields.KeywordField()}),
        'code1c': fields.TextField(fields={'raw': fields.KeywordField()}),
    })

    legalEntity = fields.ObjectField(properties={
        'first_name': fields.TextField(fields={'raw': fields.KeywordField()}),
        'middle_name': fields.TextField(),
        'last_name': fields.TextField(),
        'description': fields.TextField(fields={'raw': fields.KeywordField()}),
        'keyword': fields.TextField(fields={'raw': fields.KeywordField()}),
        'additional_name': fields.TextField(fields={'raw': fields.KeywordField()}),
    })

    typeOfPlace = fields.ObjectField(properties={
        'name': fields.TextField(fields={'raw': fields.KeywordField()}),
        'abbreviation': fields.TextField(fields={'raw': fields.KeywordField()}),
        'tariff': fields.TextField(),
        'tariff_single': fields.TextField(),
        'code1c': fields.TextField(fields={'raw': fields.KeywordField()}),
        'is_mall': fields.BooleanField(),
    })

    responsible_radio = fields.ObjectField(properties={
        'email': fields.TextField(fields={'raw': fields.KeywordField()}),
        'first_name': fields.TextField(),
        'last_name': fields.TextField(),
        'full_name': fields.TextField(),
    })

    responsible_ad = fields.ObjectField(properties={
        'email': fields.TextField(fields={'raw': fields.KeywordField()}),
        'first_name': fields.TextField(),
        'last_name': fields.TextField(),
        'full_name': fields.TextField(),
    })

    responsible_technic = fields.ObjectField(properties={
        'email': fields.TextField(fields={'raw': fields.KeywordField()}),
        'first_name': fields.TextField(),
        'last_name': fields.TextField(),
        'full_name': fields.TextField(),
    })

    responsible_technic_on_address = fields.ObjectField(properties={
        'email': fields.TextField(fields={'raw': fields.KeywordField()}),
        'first_name': fields.TextField(),
        'last_name': fields.TextField(),
        'full_name': fields.TextField(),
    })

    responsible_placement_marketing = fields.ObjectField(properties={
        'email': fields.TextField(fields={'raw': fields.KeywordField()}),
        'first_name': fields.TextField(),
        'last_name': fields.TextField(),
        'full_name': fields.TextField(),
    })

    # --- Вложенные арендаторы ---
    tenants_data = fields.NestedField(properties={
        'tenant': fields.ObjectField(properties={
            'first_name': fields.TextField(fields={'raw': fields.KeywordField()}),
            'middle_name': fields.TextField(),
            'last_name': fields.TextField(),
            'description': fields.TextField(fields={'raw': fields.KeywordField()}),
            'keyword': fields.TextField(fields={'raw': fields.KeywordField()}),
            'additional_name': fields.TextField(fields={'raw': fields.KeywordField()}),
        }),
        'floor': fields.TextField(fields={'raw': fields.KeywordField()}),
        'atm': fields.BooleanField(),
        'brand': fields.ObjectField(properties={
            'name': fields.TextField(fields={'raw': fields.KeywordField()}),
            'code1c': fields.TextField(fields={'raw': fields.KeywordField()}),
        })
    })

    # --- Общее агрегированное поле для "искать вообще везде" ---
    search_text = fields.TextField(analyzer='ru_ngram_analyzer')

    class Index:
        name = 'nomenclature'  # имя индекса
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'analysis': {
                'filter': {
                    'russian_stop': {'type': 'stop', 'stopwords': '_russian_'},
                    'russian_stemmer': {'type': 'stemmer', 'language': 'russian'},
                    'edge_ngram_filter': {'type': 'edge_ngram', 'min_gram': 2, 'max_gram': 20}
                },
                'analyzer': {
                    'ru_text_analyzer': {
                        'tokenizer': 'standard',
                        'filter': ['lowercase', 'russian_stop', 'russian_stemmer']
                    },
                    'ru_ngram_analyzer': {
                        'tokenizer': 'standard',
                        'filter': ['lowercase', 'edge_ngram_filter']
                    }
                }
            }
        }

    class Django:
        model = Nomenclature
        related_models = []

    def get_queryset(self, filter_=None, exclude=None, count=None, alias=None):
        return (
            super().get_queryset(filter_=filter_, exclude=exclude, count=count, alias=alias)
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
                'nomenclature_tenants__brand',
            )
        )

    def prepare_is_active(self, instance):
        return instance.is_active

    def prepare_brand(self, instance):
        if not instance.brand:
            return None

        return {
            'name': getattr(instance.brand, 'name', '') or '',
            'code1c': getattr(instance.brand, 'code1c', '') or '',
        }

    def prepare_legalEntity(self, instance):
        if not instance.legalEntity:
            return None

        return {
            'first_name': getattr(instance.legalEntity, 'first_name', '') or '',
            'middle_name': getattr(instance.legalEntity, 'middle_name', '') or '',
            'last_name': getattr(instance.legalEntity, 'last_name', '') or '',
            'description': getattr(instance.legalEntity, 'description', '') or '',
            'keyword': getattr(instance.legalEntity, 'keyword', '') or '',
            'additional_name': getattr(instance.legalEntity, 'additional_name', '') or '',
        }

    def prepare_typeOfPlace(self, instance):
        if not instance.typeOfPlace:
            return None

        return {
            'name': instance.typeOfPlace.name or '',
            'abbreviation': instance.typeOfPlace.abbreviation or '',
            'tariff': instance.typeOfPlace.tariff or '',
            'tariff_single': instance.typeOfPlace.tariff_single or '',
            'code1c': instance.typeOfPlace.code1c or '',
            'is_mall': instance.typeOfPlace.is_mall,
        }

    def _prepare_user(self, user):
        if not user:
            return None

        first_name = getattr(user, 'first_name', '') or ''
        last_name = getattr(user, 'last_name', '') or ''
        full_name = f'{first_name} {last_name}'.strip()

        return {
            'email': getattr(user, 'email', '') or '',
            'first_name': first_name,
            'last_name': last_name,
            'full_name': full_name,
        }

    def prepare_responsible_radio(self, instance):
        return self._prepare_user(instance.responsible_radio)

    def prepare_responsible_ad(self, instance):
        return self._prepare_user(instance.responsible_ad)

    def prepare_responsible_technic(self, instance):
        return self._prepare_user(instance.responsible_technic)

    def prepare_responsible_technic_on_address(self, instance):
        return self._prepare_user(instance.responsible_technic_on_address)

    def prepare_responsible_placement_marketing(self, instance):
        return self._prepare_user(instance.responsible_placement_marketing)

    def prepare_tenants_data(self, instance):
        result = []

        for item in instance.nomenclature_tenants.all():
            tenant = item.tenant
            brand = item.brand

            result.append({
                'tenant': {
                    'first_name': getattr(tenant, 'first_name', '') or '',
                    'middle_name': getattr(tenant, 'middle_name', '') or '',
                    'last_name': getattr(tenant, 'last_name', '') or '',
                    'description': getattr(tenant, 'description', '') or '',
                    'keyword': getattr(tenant, 'keyword', '') or '',
                    'additional_name': getattr(tenant, 'additional_name', '') or '',
                },
                'floor': item.floor or '',
                'atm': item.atm,
                'brand': {
                    'name': getattr(brand, 'name', '') if brand else '',
                    'code1c': getattr(brand, 'code1c', '') if brand else '',
                } if brand else None
            })

        return result

    def prepare_search_text(self, instance):
        parts = [
            instance.name or '',
            instance.code1c or '',
            instance.description or '',
            instance.id_rasb or '',
        ]

        # typeOfPlace
        if instance.typeOfPlace:
            parts.extend([
                instance.typeOfPlace.name or '',
                instance.typeOfPlace.abbreviation or '',
                instance.typeOfPlace.tariff or '',
                instance.typeOfPlace.tariff_single or '',
                instance.typeOfPlace.code1c or '',
            ])

        # brand
        if instance.brand:
            parts.extend([
                getattr(instance.brand, 'name', '') or '',
                getattr(instance.brand, 'code1c', '') or '',
            ])

        # legalEntity
        if instance.legalEntity:
            parts.extend([
                getattr(instance.legalEntity, 'first_name', '') or '',
                getattr(instance.legalEntity, 'first_name', '') or '',
                getattr(instance.legalEntity, 'middle_name', '') or '',
                getattr(instance.legalEntity, 'description', '') or '',
                getattr(instance.legalEntity, 'keyword', '') or '',
                getattr(instance.legalEntity, 'additional_name', '') or '',
            ])
        # users
        users = [
            instance.responsible_radio,
            instance.responsible_ad,
            instance.responsible_technic,
            instance.responsible_technic_on_address,
            instance.responsible_placement_marketing,
        ]

        for user in users:
            if user:
                parts.extend([
                    getattr(user, 'email', '') or '',
                    getattr(user, 'first_name', '') or '',
                    getattr(user, 'last_name', '') or '',
                ])

        # tenants
                # tenants
        for item in instance.nomenclature_tenants.all():
            if item.tenant:
                parts.extend([
                    getattr(item.tenant, 'first_name', '') or '',
                    getattr(item.tenant, 'middle_name', '') or '',
                    getattr(item.tenant, 'last_name', '') or '',
                    getattr(item.tenant, 'description', '') or '',
                    getattr(item.tenant, 'keyword', '') or '',
                    getattr(item.tenant, 'additional_name', '') or '',
                ])

            if item.brand:
                parts.extend([
                    getattr(item.brand, 'name', '') or '',
                    getattr(item.brand, 'code1c', '') or '',
                ])

            parts.extend([
                item.floor or '',
                'банкомат' if item.atm else '',
            ])

        return ' '.join(filter(None, parts))