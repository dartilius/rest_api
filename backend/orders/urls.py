from django.urls import include, path
from rest_framework.routers import SimpleRouter

from orders.unified_views import UnifiedOrderViewSet
from orders.views import AdOrderViewSet, BgOrderViewSet

router = SimpleRouter()

router.register(
    'adorders',
    AdOrderViewSet,
    basename='adorders'
)
router.register(
    'bgorders',
    BgOrderViewSet,
    basename='bgorders'
)
router.register(
    'broadcast-orders',
    UnifiedOrderViewSet,
    basename='broadcast-orders',
)

urlpatterns = [
    path('', include(router.urls))
]
