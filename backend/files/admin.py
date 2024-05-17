from django.contrib import admin

from files.models import File, Playlist, Tag


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    """Файл."""

    list_display = (
        'id',
        'name',
        'owner',
        'length',
        'size',
        'created'
    )
    search_fields = (
        'id',
        'name',
        'owner'
    )

    def get_queryset(self, request):
        return File.objects.all().select_related(
            'owner'
        ).prefetch_related('tags')

    def save_model(self, request, obj, form, change):
        obj.owner = obj.owner or request.user
        obj.save()


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    """Плейлисты."""

    list_display = (
        'id',
        'name',
        'description',
        'owner'
    )
    search_fields = (
        'id',
        'name',
        'owner',
    )

    def get_queryset(self, request):
        return Playlist.objects.all().select_related(
            'owner'
        ).prefetch_related('files')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Тематика."""

    list_display = ('id', 'name')
