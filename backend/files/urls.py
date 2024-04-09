from django.urls import include, path
from rest_framework.routers import SimpleRouter

from files.views import (
    FileViewSet,
    PlaylistViewSet,
    PlaylistSettingsViewSet,
    PlaylistFilesViewSet
)

router = SimpleRouter()

router.register(
    'files',
    FileViewSet,
    basename='files'
)
router.register(
    'playlists',
    PlaylistViewSet,
    basename='playlists'
)
router.register(
    r'playlists/(?P<playlist_id>[^/.]+)/settings',
    PlaylistSettingsViewSet,
    basename='playlist_settings'
)
router.register(
    r'playlists/(?P<playlist_id>[^/.]+)/files',
    PlaylistFilesViewSet,
    basename='playlist_files'
)

urlpatterns = [
    path('', include(router.urls))
]
