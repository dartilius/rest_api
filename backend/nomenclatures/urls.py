from django.urls import include, path
from rest_framework.routers import SimpleRouter

from nomenclatures.views import (
    NomenclatureViewSet,
    NomenclatureGroupViewSet
)

router = SimpleRouter()

router.register(
    'nomenclatures',
    NomenclatureViewSet,
    basename='nomenclatures'
)
router.register(
    'groups',
    NomenclatureGroupViewSet,
    basename='nomenclature_groups'
)

urlpatterns = [
    path('', include(router.urls))
]
