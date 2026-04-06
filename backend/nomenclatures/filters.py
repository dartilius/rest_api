import uuid
from django.db import models
from django_filters import (
    AllValuesMultipleFilter, CharFilter, FilterSet, UUIDFilter,
    BaseInFilter, OrderingFilter, BooleanFilter
)
from nomenclatures.models import Nomenclature, NomenclatureTenant


class UUIDCommaInFilter(BaseInFilter, UUIDFilter):
    """Поддерживает фильтрацию UUID через запятую (в URL)."""

    def filter(self, qs, value):
        if value and isinstance(value, str):
            # Убираем пустые значения
            value = [v.strip() for v in value.split(",") if v.strip()]
        return super().filter(qs, value)

def full_text_search(queryset, value):
    if not value:
        return queryset

    import logging
    logger = logging.getLogger(__name__)

    try:
        from nomenclatures.documents import NomenclatureDocument
        from opensearchpy import OpenSearchException

        search = NomenclatureDocument.search().query(
            'multi_match',
            query=value,
            fields=[
                'name^4',
                'code1c^4',
                'brand_name^3',
                'legal_entity_text^2',
                'type_of_place^2',
                'content_type',
                'tenants_text^2',
                'responsible_radio_text',
                'responsible_ad_text',
                'responsible_technic_text',
                'responsible_technic_on_address_text',
                'responsible_placement_marketing_text',
                'version',
            ],
            type='best_fields',
            fuzziness='AUTO',
            prefix_length=1,
        )

        # Получаем IDs из OpenSearch, потом фильтруем Django QS
        # чтобы сохранить все related/prefetch и фильтры
        response = search[:200].execute()
        ids = [hit.meta.id for hit in response]

        logger.info(
            'OpenSearch: запрос="%s", найдено=%d, ids=%s',
            value, len(ids), ids[:5]
        )



        if not ids:
            return queryset.none()

        # Сохраняем порядок из OpenSearch
        from django.db.models import Case, When
        preserved_order = Case(
            *[When(pk=pk, then=pos) for pos, pk in enumerate(ids)]
        )
        return queryset.filter(pk__in=ids).order_by(preserved_order)



    except Exception as e:

        logger.error('OpenSearch недоступен, фолбэк: %s', e)  # если видишь это — идёт фолбэк

        return queryset.filter(name__icontains=value)


class NomenclatureFilter(FilterSet):
    """
    Фильтрация номенклатур БЕЗ специфичных адресных фильтров.

    Для фильтрации по адресам используйте отдельное API адресов.
    Универсальный поиск (search) уже включает поиск по адресным полям.
    """

    # ==========================================================================
    # СУЩЕСТВУЮЩИЕ ФИЛЬТРЫ НОМЕНКЛАТУР
    # ==========================================================================

    search = CharFilter(method='filter_full_text',  label='Универсальный поиск')

    versions = AllValuesMultipleFilter(field_name='version')
    version = CharFilter(field_name='version', lookup_expr='icontains')
    status = CharFilter(method='get_status', label='Статус')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    id = CharFilter(field_name='id', lookup_expr='iexact')
    timezone = CharFilter(field_name='timezone', lookup_expr='iexact')
    brand_id = UUIDCommaInFilter(field_name='brand_id', lookup_expr='in')
    code1c = CharFilter(field_name='code1c', lookup_expr='iexact')

    # Новые поля для фильтрации
    legal_entity_name = CharFilter(
        field_name='legalEntity__name',
        lookup_expr='icontains',
        label='Название юридического лица'
    )

    brand_name = CharFilter(
        field_name='brand__name',
        lookup_expr='icontains',
        label='Название бренда'
    )

    type_of_place = CharFilter(
        field_name='typeOfPlace__name',
        lookup_expr='icontains',
        label='Тип места размещения'
    )

    nomenclature = CharFilter(method='filter_nomenclature_ignore', required=False)

    def filter_nomenclature_ignore(self, queryset, name, value):
        # Просто игнорируем этот параметр
        return queryset

    # ==========================================================================
    # СОРТИРОВКА (БЕЗ АДРЕСНЫХ ПОЛЕЙ)
    # ==========================================================================

    ordering = OrderingFilter(
        fields=(
            # Существующие поля номенклатур
            ('name', 'name'),
            ('version', 'version'),
            ('timezone', 'timezone'),
            ('pricePerMonth', 'pricePerMonth'),
            ('created', 'created'),
            ('brand__name', 'brand_name'),
            ('legalEntity__name', 'legal_entity_name'),
            ('typeOfPlace', 'type_place'),
        ),
        field_labels={
            # Существующие метки
            'name': 'Название',
            'version': 'Версия ПО',
            'timezone': 'Часовой пояс',
            'pricePerMonth': 'Цена',
            'created': 'Дата создания',
            'brand__name': 'Бренд',
            'legalEntity__name': 'Юр.лицо',
            'typeOfPlace': 'Тип места',
        }
    )

    class Meta:
        model = Nomenclature
        fields = (
            # Существующие поля
            'search', 'name', 'id', 'timezone', 'versions', 'status',
            'brand_id', 'code1c', 'legal_entity_name', 'brand_name',
            'type_of_place'
        )

    # ==========================================================================
    # СУЩЕСТВУЮЩИЕ МЕТОДЫ (БЕЗ ИЗМЕНЕНИЙ)
    # ==========================================================================

    def filter_full_text(self, queryset, name, value):
        return full_text_search(queryset, value)

    def get_status(self, queryset, name, value):
        """
        Специальный метод для фильтрации по статусам.
        """
        if value.lower() == 'null':
            return queryset.filter(availability__status=None)
        elif value in ('0', '1', '2'):
            return queryset.filter(availability__status=value)
        else:
            return queryset


    @property
    def qs(self):
        """
        ОПТИМИЗАЦИЯ QUERYSET ДЛЯ ВСЕХ ЗАПРОСОВ.
        """
        queryset = super().qs

        # Оптимизация только для списковых запросов
        if not self.request or 'pk' not in self.request.parser_context.get('kwargs', {}):
            queryset = queryset.select_related(
                # Существующие связи
                'brand',
                'legalEntity',
                'responsible_radio',
                'responsible_ad',
                'availability',

                # Связи для адресов (для has_address и поиска)
                'address__address',
            ).prefetch_related(
                'tenants'
            )

        return queryset


class NomenclatureTenantFilter(FilterSet):
    floor = CharFilter(field_name="floor", lookup_expr="exact")

    class Meta:
        model = NomenclatureTenant
        fields = ["floor"]

# ==============================================================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ (УПРОЩЕННЫЕ)
# ==============================================================================

"""
1. Поиск по адресу через универсальный поиск:
   GET /api/nomenclatures/?search=Красноярск Ленина

2. Поиск по названию номенклатуры:
   GET /api/nomenclatures/?search=Номенклатура1

3. Фильтрация по бренду:
   GET /api/nomenclatures/?brand_id=uuid1,uuid2

5. Фильтрация по статусу:
   GET /api/nomenclatures/?status=0

📌 ДЛЯ СЛОЖНОЙ ФИЛЬТРАЦИИ ПО АДРЕСАМ:
   Используйте API адресов для получения ID адресов,
   затем фильтруйте номенклатуры по address__address_id

   Пример:
   1. Сначала найдите адреса: GET /api/addresses/?search=Москва Ленина
   2. Получите ID адресов
   3. Найдите номенклатуры: GET /api/nomenclatures/?address__address_id=uuid1,uuid2
"""
