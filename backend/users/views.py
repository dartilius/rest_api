from uuid import UUID

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_204_NO_CONTENT, HTTP_201_CREATED
)
from rest_framework.views import APIView

from api.constants import DEFAULT_SCHEMA_RESPONSES, DEFAULT_SCHEMA_EXAMPLES
from users.filters import CustomUserFilter
from users.models import CustomUser
from users.permissions import SuperuserCUDAuthRetrieve
from users.serializers import CustomUserSerializer, RegisterUserSerializer, \
    CustomUserShortSerializer, PasswordResetByEmailSerializer, GetPasswordSerializer


@extend_schema_view(
    list=extend_schema(
        summary="Получить пагинированный список пользователей (кл)",
        description=(
                "Возвращает постраничный список пользователей. (кл) "
                "Использует `CustomUserShortSerializer`."
        ),
        responses={
            200: OpenApiResponse(
                response=CustomUserShortSerializer,
                description="Успешное получение списка пользователей (кл)",
                examples=[
                    OpenApiExample(
                        name="Список",
                        value={
                            "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                            "full_name": {
                                "last_name": "string",
                                "first_name": "string",
                                "middle_name": "string"
                            }
                        }

                    )

                ],

            ),
            **DEFAULT_SCHEMA_RESPONSES
        },
    ),

    retrieve=extend_schema(
        summary="Получить расшифровку пользователя (кл)",
        description="Возвращает полное описание пользователя (кл) через `CustomUserSerializer`.",
        responses={
            200: CustomUserSerializer,
            **DEFAULT_SCHEMA_RESPONSES
        }
    ),

    partial_update=extend_schema(
        summary="Частичное обновление пользователя (кл)",
        request=CustomUserSerializer,
        responses={
            200: CustomUserShortSerializer,
            **DEFAULT_SCHEMA_RESPONSES,
        }
    ),

    destroy=extend_schema(
        summary="Удалить пользователя (кл)",
        examples=[
                     OpenApiExample(
                         "Пользователь (кл) успешно удалён",
                         status_codes=[HTTP_204_NO_CONTENT],
                         response_only=True,
                     )
                 ] + DEFAULT_SCHEMA_EXAMPLES,
        responses={HTTP_204_NO_CONTENT: {}} | DEFAULT_SCHEMA_RESPONSES,
    ),
)
@extend_schema(tags=['Пользователи (кл)'])

class CustomUserViewSet(viewsets.ModelViewSet):
    """Работа с пользователями."""
    lookup_field = "id_or_code1c"
    queryset = CustomUser.objects.all().order_by('id')
    filter_backends = [DjangoFilterBackend]
    filterset_class = CustomUserFilter
    permission_classes = [SuperuserCUDAuthRetrieve]

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

        # пробуем code1c; code1c не уникален, поэтому берём последнюю активную запись
        customUser = (
            CustomUser.objects
            .filter(code1c=identifier, is_active=True)
            .order_by("-created", "id")
            .first()
        )
        if customUser is None:
            raise NotFound("Пользователь не найден.")
        return customUser

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

    def get_serializer_class(self):
        if self.action == 'list':
            return CustomUserShortSerializer
        return CustomUserSerializer

    @extend_schema(
        summary="Регистрация нового пользователя",
        description=(
                "Создает нового пользователя в системе по email, имени, фамилии, "
                "телефону и паролю. Возвращает идентификатор созданного пользователя."
        ),
        request=RegisterUserSerializer,
        responses={
            201: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        name="Успешная регистрация",
                        value={
                            "detail": "Регистрация успешна",
                            "id": "0f6130ab-60f8-4e3b-9b01-bcc23f6b8216"
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                description="Ошибка валидации",
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        name="Пример ошибки",
                        value={
                            "email": ["Пользователь с таким email уже существует"]
                        },
                    )
                ],
            ),
        },
    )
    @action(methods=['post'], url_path="register", url_name="register", detail=False, permission_classes=[AllowAny])
    def register(self, request, *args, **kwargs):
        serializer = RegisterUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data

        user = CustomUser(
            email=validated["email"],
            first_name=validated["first_name"],
            last_name=validated["last_name"],
            phone_number=validated["phone_number"],
        )
        user.set_password(validated["password"])
        user.save()

        return Response(
            {"detail": "Регистрация успешна", "id": str(user.id)},
            status=HTTP_201_CREATED
        )

    @extend_schema(
        summary="Сброс пароля по email",
        request=PasswordResetByEmailSerializer,
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                examples=[OpenApiExample(name="Успешно", value={"detail": "Пароль успешно изменён."})]
            ),
            **DEFAULT_SCHEMA_RESPONSES,
        }
    )
    @action(
        methods=['post'],
        url_path="reset-password",
        url_name="reset-password",
        detail=False,
        permission_classes=[AllowAny],
    )
    def reset_password(self, request, *args, **kwargs):
        serializer = PasswordResetByEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data

        try:
            user = CustomUser.objects.get(email=validated['email'], is_active=True)
        except CustomUser.DoesNotExist:
            raise NotFound("Пользователь с таким email не найден.")

        user.set_password(validated['new_password'])
        user.save(update_fields=['password'])

        return Response({"detail": "Пароль успешно изменён."})

    @action(methods=['get'], url_path="get-password", url_name="get-password", detail=True)
    def get_password(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = GetPasswordSerializer(user)
        return Response(serializer.data)


@extend_schema(
    tags=['Пользователи (кл)'],
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
