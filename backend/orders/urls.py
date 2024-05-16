from django.urls import include, path
from rest_framework.routers import SimpleRouter

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

urlpatterns = [
    path('', include(router.urls))
]
