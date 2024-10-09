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
    id = CharFilter(field_name='id', lookup_expr='exact')
    file_type = CharFilter(field_name='file_type', lookup_expr='exact')
    tags = AllValuesMultipleFilter(field_name='tags__name')

    class Meta:
        model = File
        fields = ('id', 'name', 'file_type', 'tags', 'hash')


class PlaylistFilter(FilterSet):
    """
    Фильтрация плейлистов.

    Выполняется по полям:
        id      - точное совпадение
        name    - частичное совпадение
    """

    id = CharFilter(field_name='id', lookup_expr='exact')
    name = CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Playlist
        fields = ('id', 'name')
