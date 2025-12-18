from django.db import models
from django_filters import AllValuesMultipleFilter, CharFilter, FilterSet, UUIDFilter, BaseInFilter, OrderingFilter
from nomenclatures.models import Nomenclature


class UUIDCommaInFilter(BaseInFilter, UUIDFilter):
    """Поддерживает фильтрацию UUID через запятую (в URL)."""

    def filter(self, qs, value):
        if value and isinstance(value, str):
            value = value.split(",")
        return super().filter(qs, value)


class NomenclatureFilter(FilterSet):
    """
    Фильтрация номенклатур.
    """

    search = CharFilter(method='universal_search', label='Универсальный поиск')

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
        field_name='typeOfPlace',
        lookup_expr='icontains',
        label='Тип места размещения'
    )

    ordering = OrderingFilter(
        fields=(
            ('name', 'name'),
            ('version', 'version'),
            ('timezone', 'timezone'),
            ('pricePerMonth', 'pricePerMonth'),
            ('created', 'created'),
            ('brand__name', 'brand_name'),
            ('legalEntity__name', 'legal_entity_name'),
        ),
        field_labels={
            'name': 'Название',
            'version': 'Версия ПО',
            'timezone': 'Часовой пояс',
            'pricePerMonth': 'Цена за месяц',
            'created': 'Дата создания',
            'brand__name': 'Название бренда',
            'legalEntity__name': 'Юридическое лицо',
        }
    )

    class Meta:
        model = Nomenclature
        fields = ('search', 'name', 'id', 'timezone', 'versions', 'status', 'brand_id', 'code1c')

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

    def universal_search(self, queryset, name, value):
        """
        Универсальный поиск по номенклатурам и связанным сущностям.
        Ищет ТОЛЬКО по реальным полям БД.
        """
        if not value:
            return queryset

        q = models.Q()

        # =========================
        # Nomenclature (свои поля)
        # =========================
        q |= models.Q(name__icontains=value)
        q |= models.Q(version__icontains=value)
        q |= models.Q(code1c__icontains=value)
        q |= models.Q(typeOfPlace__icontains=value)

        # =========================
        # Brand
        # =========================
        q |= models.Q(brand__name__icontains=value)

        # =========================
        # LegalEntity (Counterparty FK)
        # =========================
        q |= models.Q(legalEntity__first_name__icontains=value)
        q |= models.Q(legalEntity__middle_name__icontains=value)
        q |= models.Q(legalEntity__last_name__icontains=value)
        q |= models.Q(legalEntity__keyword__icontains=value)
        q |= models.Q(legalEntity__description__icontains=value)
        q |= models.Q(legalEntity__brands__name__icontains=value)

        # =========================
        # Tenants (Counterparty M2M)
        # =========================
        q |= models.Q(tenants__first_name__icontains=value)
        q |= models.Q(tenants__middle_name__icontains=value)
        q |= models.Q(tenants__last_name__icontains=value)
        q |= models.Q(tenants__keyword__icontains=value)
        q |= models.Q(tenants__description__icontains=value)
        q |= models.Q(tenants__brands__name__icontains=value)

        # =========================
        # Responsible radio
        # =========================
        q |= models.Q(responsible_radio__email__icontains=value)
        q |= models.Q(responsible_radio__first_name__icontains=value)
        q |= models.Q(responsible_radio__middle_name__icontains=value)
        q |= models.Q(responsible_radio__last_name__icontains=value)
        q |= models.Q(responsible_radio__phone_number__icontains=value)
        q |= models.Q(responsible_radio__code1c__icontains=value)

        # =========================
        # Responsible ad
        # =========================
        q |= models.Q(responsible_ad__email__icontains=value)
        q |= models.Q(responsible_ad__first_name__icontains=value)
        q |= models.Q(responsible_ad__middle_name__icontains=value)
        q |= models.Q(responsible_ad__last_name__icontains=value)
        q |= models.Q(responsible_ad__phone_number__icontains=value)
        q |= models.Q(responsible_ad__code1c__icontains=value)

        return queryset.filter(q).distinct()