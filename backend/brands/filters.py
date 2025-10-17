from django_filters import CharFilter, FilterSet, BooleanFilter
from brands.models import Brand


class BrandFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains")
    code1c = CharFilter(field_name="code1c", lookup_expr="icontains")
    is_deleted = BooleanFilter(field_name="is_deleted")

    class Meta:
        model = Brand
        fields = ["name", "code1c", "is_deleted"]
