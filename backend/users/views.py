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
from users.permissions import SuperuserCUDAuthRetrieve
from users.serializers import CustomUserSerializer, CustomUserListSerializer


class CustomUserViewSet(viewsets.ModelViewSet):
    """Работа с пользователями."""

    queryset = CustomUser.objects.all().order_by('id')
    serializer_class = CustomUserSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CustomUserFilter
    permission_classes = [SuperuserCUDAuthRetrieve]

    def perform_create(self, serializer):
        user = serializer.save()
        user.set_password(self.request.data['password'])
        user.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.perform_destroy(instance)
        return Response(data=data, status=400 if data else 204)

    def perform_destroy(self, instance):
        if instance.is_active is True:
            instance.is_active = False
            instance.save(update_fields=['is_active'])
            return None
        else:
            return (
                'Пользователь уже помечен как "неактуальный". '
                'Удалить его можно только через админ-панель.'
            )

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
