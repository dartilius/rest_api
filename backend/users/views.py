from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_204_NO_CONTENT
)

from users.filters import CustomUserFilter
from users.models import CustomUser
from users.serializers import CustomUserSerializer, CustomUserListSerializer


class CustomUserViewSet(viewsets.ModelViewSet):
    """Работа с пользователями."""

    queryset = CustomUser.objects.all().order_by('id')
    serializer_class = CustomUserSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CustomUserFilter
    # permission_classes = [IsSuperUserOrAuthReadOnly, ]

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            serializer = CustomUserListSerializer
        else:
            serializer = CustomUserSerializer
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return serializer(*args, **kwargs)


@api_view(['POST'])
def logout(request):
    """Выход из системы."""
    if not request.user.is_authenticated:
        return Response(
            {'message': 'Пользователь не авторизован.'},
            status=HTTP_401_UNAUTHORIZED
        )
    request.auth.blacklist()
    return Response(
        {'message': 'Вы вышли из системы.'},
        status=HTTP_204_NO_CONTENT
    )
