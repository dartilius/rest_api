from rest_framework.routers import SimpleRouter
from django.urls import include, path

from brands.views import BrandViewSet

router = SimpleRouter()

router.register("brands", BrandViewSet, basename="brands")

urlpatterns = [path("", include(router.urls))]
