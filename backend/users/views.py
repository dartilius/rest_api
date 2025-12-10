from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_204_NO_CONTENT
)
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from uuid import UUID
from counterparties.serializers import CounterpartiesSerializer
from users.filters import CustomUserFilter
from users.models import CustomUser
from users.permissions import SuperuserCUDAuthRetrieve
from users.serializers import CustomUserSerializer, CustomUserListSerializer


@extend_schema(tags=['users'])
class CustomUserViewSet(viewsets.ModelViewSet):
    """Работа с пользователями."""
    lookup_field = "id_or_code1c"
    queryset = CustomUser.objects.all().order_by('id')
    serializer_class = CustomUserSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CustomUserFilter
    permission_classes = [SuperuserCUDAuthRetrieve]

    @action(detail=False, methods=['get'])
    def get_mine_counterparties(self, request):
        """Получить контрагентов текущего пользователя."""
        user = request.user
        if not user.is_authenticated:
            return Response({'message': 'Пользователь не авторизован.'}, status=HTTP_401_UNAUTHORIZED)

        mine_counterparties = user.counterparties.all()

        # Пагинация, если настроена
        page = self.paginate_queryset(mine_counterparties)
        if page is not None:
            serializer = CounterpartiesSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Без пагинации
        serializer = CounterpartiesSerializer(mine_counterparties, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        user = serializer.save()
        user.set_password(self.request.data['password'])
        user.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.perform_destroy(instance)
        return Response(
            data={'detail': data} if data else None,
            status=400 if data else 204
        )

    def get_object(self):
        identifier = self.kwargs.get(self.lookup_field)
        if not identifier:
            raise NotFound("Не указан идентификатор пользователя.")

        # пробуем UUID
        try:
            uuid_obj = UUID(str(identifier))
            customUser = CustomUser.objects.get(id=uuid_obj)
            if customUser.is_active is False:
                raise NotFound("Пользователь не найден.")
            return customUser
        except (ValueError, CustomUser.DoesNotExist):
            pass

        # пробуем code1c
        try:
            customUser = CustomUser.objects.get(code1c=identifier)
            if customUser.is_active is False:
                raise NotFound("Пользователь не найден.")
            return customUser
        except CustomUser.DoesNotExist:
            raise NotFound("Пользователь не найден.")

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


@extend_schema(
    tags=['users'],
    responses={
        204: None,
        401: None
    }
)
class LogoutView(APIView):
    """Выход из системы."""

    def post(self, request):
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
