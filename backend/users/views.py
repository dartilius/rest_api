from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
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


@extend_schema(tags=['users'])
class CustomUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с пользователями.
    
    Обеспечивает CRUD операции для пользователей с фильтрацией.
    """
    
    queryset = CustomUser.objects.all().order_by('id')
    serializer_class = CustomUserSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CustomUserFilter
    permission_classes = [SuperuserCUDAuthRetrieve]

    def perform_create(self, serializer):
        """
        Создает пользователя с хешированием пароля.
        
        Args:
            serializer: Сериализатор пользователя
        """
        user = serializer.save()
        user.set_password(self.request.data['password'])
        user.save()

    def destroy(self, request, *args, **kwargs):
        """
        Мягкое удаление пользователя.
        
        Помечает пользователя как неактивного вместо физического удаления.
        """
        instance = self.get_object()
        data = self.perform_destroy(instance)
        return Response(
            data={'detail': data} if data else None,
            status=400 if data else 204
        )

    def perform_destroy(self, instance):
        """
        Выполняет мягкое удаление пользователя.
        
        Args:
            instance: Объект пользователя
            
        Returns:
            str | None: Сообщение об ошибке или None при успехе
        """
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
        """
        Возвращает соответствующий сериализатор в зависимости от действия.
        
        Для списка использует краткий сериализатор, для остального - полный.
        """
        if self.action == 'list':
            serializer = CustomUserListSerializer
        else:
            serializer = CustomUserSerializer
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return serializer(*args, **kwargs)


@extend_schema(
    tags=['users'],
    responses={
        204: None,  # Успешный выход без содержимого
        401: None   # Неавторизованный запрос
    }
)
@api_view(['POST'])
def logout(request):
    """
    Выход пользователя из системы.
    
    Добавляет токен в черный список для предотвращения повторного использования.
    
    Returns:
        Response: Сообщение о успешном выходе или ошибке авторизации
    """
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
