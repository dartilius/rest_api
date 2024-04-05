from django.urls import include, path
from rest_framework.routers import SimpleRouter

from nomenclatures.views import NomenclatureViewSet, HardWareInfoViewSet, SettingsViewSet, \
    NomenclatureGroupSerializerViewSet

router = SimpleRouter()

router.register(
    'nomenclatures',
    NomenclatureViewSet,
    basename='nomenclatures'
)
router.register(
    r'nomenclatures/(?P<nomenclature_id>[^/.]+)/hw_info',
    HardWareInfoViewSet,
    basename='hw_info'
)
router.register(
    r'nomenclatures/(?P<nomenclature_id>[^/.]+)/settings',
    SettingsViewSet,
    basename='settings'
)
router.register(
    'groups',
    NomenclatureGroupSerializerViewSet,
    basename='nomenclature_groups'
)

urlpatterns = [
    path('', include(router.urls))
]
