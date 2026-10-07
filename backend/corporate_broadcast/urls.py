from rest_framework.routers import DefaultRouter
from .views import BroadcastDemoViewSet

router = DefaultRouter()
router.register("broadcast-demos", BroadcastDemoViewSet, basename="broadcast-demo")
urlpatterns = router.urls
