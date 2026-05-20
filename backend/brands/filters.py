from django_filters import CharFilter, FilterSet, BooleanFilter
from brands.models import Brand


class BrandFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains")
    code1c = CharFilter(field_name="code1c", lookup_expr="icontains")
    is_deleted = BooleanFilter(field_name="is_deleted")
    # search — обрабатывается отдельно во вьюсете через OpenSearch,
    # здесь только чтобы он не падал как неизвестный параметр
    search = CharFilter(method="noop", label="Полнотекстовый поиск")

    def noop(self, queryset, name, value):
        return queryset

    class Meta:
        model = Brand
        fields = ["name", "code1c", "is_deleted", "search"]