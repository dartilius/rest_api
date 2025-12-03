from rest_framework.routers import SimpleRouter
from django.urls import include, path
from promotions.views import PromotionViewSet

router = SimpleRouter()

router.register("promotions", PromotionViewSet, basename="promotions")

urlpatterns = [path("", include(router.urls))]
