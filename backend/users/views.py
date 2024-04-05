from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from users.models import User
from users.permissions import IsSuperUserOrAuthReadOnly
from users.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """Работа с пользователями."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = LimitOffsetPagination
    # permission_classes = [IsSuperUserOrAuthReadOnly, ]
