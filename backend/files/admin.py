from django.contrib import admin

from .models import File, Playlist, Tag


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    """Файл."""

    @admin.display(description='Продолжительность')
    def full_length(self, obj):
        try:
            return f'{obj.length:%H:%M:%S}'
        except TypeError:
            return obj.length

    @admin.display(description='Размер')
    def formatted_size(self, obj):
        if obj.size // 1024 >= 1:
            formatted_tail = obj.size % 1048576 // 1000
            return f'{obj.size // 1048576}.{formatted_tail}Mb'
        else:
            return f'{obj.size // 1024}Kb'

    list_display = (
        'id',
        'name',
        'owner',
        'full_length',
        'formatted_size',
        'is_active',
        'created'
    )
    search_fields = ('name',)

    def get_queryset(self, request):
        return File.objects.all().select_related(
            'owner'
        )

    def save_model(self, request, obj, form, change):
        obj.owner = obj.owner or request.user
        obj.save()


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    """Плейлисты."""

    list_display = (
        'id',
        'name',
        'owner'
    )
    search_fields = ('name',)

    def get_queryset(self, request):
        return Playlist.objects.all().select_related(
            'owner'
        ).prefetch_related('files')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Тематика."""

    list_display = ('id', 'name')
