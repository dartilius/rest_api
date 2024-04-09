from django.contrib import admin

from files.models import File, Playlist, PlaylistSettings


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    """Файл."""

    list_display = (
        'id',
        'name',
        'owner',
        'length',
        'size',
        'type',
        'theme',
        'created'
    )
    search_fields = (
        'id',
        'name',
        'owner',
        'type',
        'theme'
    )

    def get_queryset(self, request):
        return File.objects.all().select_related('owner').prefetch_related(
            'settings'
        )


@admin.register(PlaylistSettings)
class PlaylistSettingsAdmin(admin.ModelAdmin):
    """Настройки плейлиста."""

    list_display = ('id', 'playlist', 'broadcast_type', 'parameters')


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    """Плейлисты."""

    list_display = (
        'id',
        'name',
        'description',
        'files',
        'settings',
        'owner',
        'created'
    )
    search_fields = (
        'id',
        'name',
        'owner',
    )


@admin.register(Playlist.files.through)
class PlaylistFilesAdmin(admin.ModelAdmin):
    """Номенклатуры группы."""
