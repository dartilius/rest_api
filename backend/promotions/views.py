from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, OpenApiResponse
from rest_framework import viewsets
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.exceptions import NotFound
from uuid import UUID

from api.constants import DEFAULT_SCHEMA_EXAMPLES, DEFAULT_SCHEMA_RESPONSES
from counterparties.models import Counterparty
from promotions.models import Promotion
from promotions.serializers import PromotionSerializer, PromotionListSerializer, PromotionOutputSerializer
from users.models import CONTACT_PERSON_ROLES


@extend_schema_view(
    list=extend_schema(
        summary="Получить пагинированный список акций",
        description=(
                "Возвращает постраничный список акций. "
                "Использует `PromotionListSerializer`."
        ),
        responses={
            200: OpenApiResponse(
                response=PromotionListSerializer,
                description="Успешное получение списка акций",

            ),
            **DEFAULT_SCHEMA_RESPONSES
        },
    ),

    retrieve=extend_schema(
        summary="Получить одну акцию",
        description="Возвращает полное описание акции через `PromotionSerializer`.",
        responses={
            200: PromotionOutputSerializer,
            **DEFAULT_SCHEMA_RESPONSES
        }
    ),

    create=extend_schema(
        summary="Создать акцию",
        description="Создаёт новую акцию. В запросе используется `PromotionSerializer`.",
        request=PromotionSerializer,
        responses={
            201: PromotionOutputSerializer,
            401: DEFAULT_SCHEMA_EXAMPLES,
            **DEFAULT_SCHEMA_RESPONSES
        }
    ),

    update=extend_schema(
        summary="Полностью обновить акцию",
        request=PromotionSerializer,
        responses={
            200: PromotionOutputSerializer,
            **DEFAULT_SCHEMA_RESPONSES,
        }
    ),

    partial_update=extend_schema(
        summary="Частично обновить акцию",
        request=PromotionSerializer,
        responses={
            200: PromotionOutputSerializer,
            **DEFAULT_SCHEMA_RESPONSES,
        }
    ),

    destroy=extend_schema(
        summary="Удалить акцию",
        examples=[
                     OpenApiExample(
                         "Акция успешна удалена",
                         status_codes=[HTTP_204_NO_CONTENT],
                         response_only=True,
                     )
                 ] + DEFAULT_SCHEMA_EXAMPLES,
        responses={HTTP_204_NO_CONTENT: {}} | DEFAULT_SCHEMA_RESPONSES,
    ),
)
@extend_schema(tags=["Акция"])
class PromotionViewSet(viewsets.ModelViewSet):
    lookup_field = 'id_or_code1c'
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    queryset = Promotion.objects.all()

    def get_serializer(self, *args, **kwargs):
        if self.action == "list":
            serializer = PromotionListSerializer
        else:
            serializer = PromotionSerializer

        return serializer(*args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        is_admin = (
                user.is_admin
                or user.is_superuser
                or user.is_ordinary
                or user.is_manager
        )

        qs = Counterparty.objects.all().order_by('id')

        if user.role in CONTACT_PERSON_ROLES:
            user_counterparties = Counterparty.objects.filter(contact_person=user)
            qs = qs.filter(
                Q(id__in=user_counterparties.values_list('id', flat=True))
            ).distinct()
        elif is_admin:
            pass  # админы видят всех

        else:
            qs = Counterparty.objects.none()
        return qs

    def get_object(self):
        identifier = self.kwargs.get(self.lookup_field)
        if not identifier:
            raise NotFound("Не указан идентификатор акции.")

        # пробуем UUID
        try:
            uuid_obj = UUID(str(identifier))
            promotion = Promotion.active.get(id=uuid_obj)
            if promotion.is_deleted:
                raise NotFound("Акция не найдена.")
            return promotion
        except (ValueError, Promotion.DoesNotExist):
            pass

        # пробуем code1c
        try:
            promotion = Promotion.active.get(code1c=identifier)
            if promotion.is_deleted:
                raise NotFound("Акция не найдена.")
            return promotion
        except Promotion.DoesNotExist:
            raise NotFound("Акция не найдена.")
