from django.urls import include, path
from rest_framework.routers import SimpleRouter

from nomenclatures.views import NomenclatureViewSet

router = SimpleRouter()

router.register(
    'nomenclatures',
    NomenclatureViewSet,
    basename='nomenclatures'
)

urlpatterns = [
    path('', include(router.urls))
]
