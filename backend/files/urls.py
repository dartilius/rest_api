from django.urls import include, path
from rest_framework.routers import SimpleRouter

from files.views import (
    FileViewSet,
    PlaylistViewSet,
    PlaylistFilesViewSet,
    TagViewSet
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
    r'playlists/(?P<playlist_id>[^/.]+)/files',
    PlaylistFilesViewSet,
    basename='playlist_files'
)
router.register(
    'files/tag',
    TagViewSet,
    basename='files_tag'
)

urlpatterns = [
    path('', include(router.urls))
]
