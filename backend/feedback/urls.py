from rest_framework.routers import DefaultRouter

from feedback.views import FeedbackViewSet

router = DefaultRouter()
router.register(r"feedback", FeedbackViewSet, basename="feedback")

urlpatterns = router.urls