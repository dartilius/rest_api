from django.urls import include, path
from rest_framework.routers import SimpleRouter

from nomenclatures.views import NomenclatureViewSet, BrandViewSet

router = SimpleRouter()

router.register("nomenclatures", NomenclatureViewSet, basename="nomenclatures")
router.register("brands", BrandViewSet, basename="brands")

urlpatterns = [path("", include(router.urls))]
