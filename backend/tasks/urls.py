from django.urls import include, path
from rest_framework.routers import SimpleRouter

from tasks.views import TaskViewSet

router = SimpleRouter()

router.register(
    'tasks',
    TaskViewSet,
    basename='tasks'
)

urlpatterns = [
    path('', include(router.urls))
]
