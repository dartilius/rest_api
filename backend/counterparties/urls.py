from rest_framework.routers import DefaultRouter
from .views import CounterpartiesViewSet

router = DefaultRouter()
router.register(r"counterparties", CounterpartiesViewSet, basename="counterparties")

urlpatterns = router.urls
