from rest_framework.routers import DefaultRouter
from .views import BroadcastDemoViewSet, BroadcastLandingViewSet

router = DefaultRouter()
router.register("broadcast-demos", BroadcastDemoViewSet, basename="broadcast-demo")
router.register("broadcast-landings", BroadcastLandingViewSet, basename="broadcast-landing")
urlpatterns = router.urls
