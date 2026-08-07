from django.db.models import Q
from django_filters import AllValuesMultipleFilter, CharFilter, FilterSet

from files.models import File, Playlist


class FileFilter(FilterSet):
    """
    Фильтрация файлов.

    Выполняется по полям:
        hash        - точное совпадение
        name        - частичное совпадение
        id          - точное совпадение
        file_type   - точное совпадение
        tags        - селектор из всех возможных вариантов
    """

    hash = CharFilter(field_name='hash', lookup_expr='iexact', label='Хэш')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    search = CharFilter(method='search_filter')
    id = CharFilter(field_name='id', lookup_expr='exact')
    file_type = CharFilter(field_name='type', lookup_expr='exact')
    tags = AllValuesMultipleFilter(field_name='tags__name')

    class Meta:
        model = File
        fields = ('id', 'name', 'search', 'file_type', 'tags', 'hash')

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(tags__name__icontains=value)
        ).distinct()


class PlaylistFilter(FilterSet):
    """
    Фильтрация плейлистов.

    Выполняется по полям:
        id      - точное совпадение
        name    - частичное совпадение
    """

    id = CharFilter(field_name='id', lookup_expr='exact')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    search = CharFilter(method='search_filter')

    class Meta:
        model = Playlist
        fields = ('id', 'name', 'search')

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(files__name__icontains=value)
        ).distinct()
