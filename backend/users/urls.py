from django.urls import include, path
from rest_framework.routers import SimpleRouter

from users.views import CustomUserViewSet

router = SimpleRouter()

router.register(
    'users',
    CustomUserViewSet,
    basename='users'
)

urlpatterns = [
    path('', include(router.urls))
]
