from django.urls import include, path
from rest_framework.routers import SimpleRouter

from files.views import (
    FileViewSet,
    PlaylistViewSet,
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
    'tags',
    TagViewSet,
    basename='tags'
)

urlpatterns = [
    path('', include(router.urls))
]
