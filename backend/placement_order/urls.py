# urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlacementOrderViewSet
from .reporting import PlacementOrderMarketingReportView

router = DefaultRouter()
router.register(r"placement-orders", PlacementOrderViewSet, basename="placement-order")

urlpatterns = [
    path(
        "marketing/placement-orders/report",
        PlacementOrderMarketingReportView.as_view(),
        name="placement-order-marketing-report",
    ),
    path("", include(router.urls)),
]
