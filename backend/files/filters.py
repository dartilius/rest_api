from django_filters import CharFilter
from django_filters.rest_framework import FilterSet

from files.models import File, Playlist


class FileFilter(FilterSet):
    """Фильтрация файлов."""

    hash = CharFilter(field_name='hash', lookup_expr='iexact', label='Хэш')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    id = CharFilter(field_name='id', lookup_expr='exact')
    file_type = CharFilter(field_name='file_type', lookup_expr='exact')
    tags = CharFilter(field_name='tags', lookup_expr='iexact')

    class Meta:
        model = File
        fields = ('id', 'name', 'file_type', 'tags', 'hash')


class PlaylistFilter(FilterSet):
    """Фильтрация плейлистов."""

    id = CharFilter(field_name='id', lookup_expr='exact')
    name = CharFilter(field_name='name', lookup_expr='iexact')

    class Meta:
        model = Playlist
        fields = ('id', 'name')


