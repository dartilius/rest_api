from django_filters import CharFilter
from django_filters.rest_framework import FilterSet

from files.models import File, Playlist


class FileFilter(FilterSet):
    """Фильтрация номенклатур."""

    hash = CharFilter(field_name='hash', lookup_expr='iexact', label='Хэш')

    class Meta:
        model = File
        fields = {
            'id': ['exact'],
            'name': ['icontains'],
            'file_type': ['exact'],
            'tags': ['iexact']
        }


class PlaylistFilter(FilterSet):
    """Фильтрация номенклатур."""

    class Meta:
        model = Playlist
        fields = {
            'id': ['exact'],
            'name': ['iexact']
        }


