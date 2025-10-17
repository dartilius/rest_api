from django_filters import rest_framework as filters
from brands.models import Brand

class BrandFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    code1c = filters.CharFilter(field_name="code1c", lookup_expr="icontains")
    is_deleted = filters.BooleanFilter(field_name="is_deleted")

    class Meta:
        model = Brand
        fields = ["name", "code1c", "is_deleted"]
