# urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlacementOrderViewSet

router = DefaultRouter()
router.register(r"placement-orders", PlacementOrderViewSet, basename="placement-order")

urlpatterns = [
    path("", include(router.urls)),
]