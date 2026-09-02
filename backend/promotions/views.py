"""ViewSet для управления акциями."""

from uuid import UUID

from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.status import HTTP_204_NO_CONTENT

from api.constants import DEFAULT_SCHEMA_EXAMPLES, DEFAULT_SCHEMA_RESPONSES
from brands.models import Brand
from promotions.models import Promotion
from promotions.serializers import PromotionListSerializer, PromotionSerializer


@extend_schema_view(
    list=extend_schema(
        summary="Получить пагинированный список акций",
        responses={200: OpenApiResponse(response=PromotionListSerializer)},
    ),
    retrieve=extend_schema(
        summary="Получить одну акцию",
        responses={200: PromotionSerializer},
    ),
    create=extend_schema(
        summary="Создать акцию",
        request=PromotionSerializer,
        responses={201: PromotionSerializer},
    ),
    update=extend_schema(request=PromotionSerializer, responses={200: PromotionSerializer}),
    partial_update=extend_schema(request=PromotionSerializer, responses={200: PromotionSerializer}),
    destroy=extend_schema(
        summary="Удалить акцию",
        examples=[
            OpenApiExample("Акция успешно удалена", status_codes=[HTTP_204_NO_CONTENT], response_only=True),
        ] + DEFAULT_SCHEMA_EXAMPLES,
        responses={HTTP_204_NO_CONTENT: {}} | DEFAULT_SCHEMA_RESPONSES,
    ),
)
@extend_schema(tags=["Акция"])
class PromotionViewSet(viewsets.ModelViewSet):
    lookup_field = "id_or_code1c"
    http_method_names = ["get", "post", "put", "patch", "delete"]
    queryset = Promotion.objects.all()

    def get_queryset(self):
        queryset = (
            Promotion.objects
            .select_related("counterparty")
            .prefetch_related(
                Prefetch(
                    "counterparty__brands",
                    queryset=Brand.objects.only("id", "name", "description"),
                    to_attr="_prefetched_brands",
                ),
            )
            .order_by("-created")
        )
        user = self.request.user
        if user.is_employee:
            return queryset
        if user.is_contact_person:
            return queryset.filter(counterparty__contact_persons=user)
        return queryset.none()

    def get_serializer_class(self):
        return PromotionListSerializer if self.action == "list" else PromotionSerializer

    def get_object(self):
        identifier = self.kwargs.get(self.lookup_field)
        if not identifier:
            raise NotFound("Не указан идентификатор акции.")

        queryset = self.get_queryset().filter(is_active=True)
        try:
            promotion = queryset.filter(id=UUID(str(identifier))).first()
        except ValueError:
            promotion = None
        if promotion:
            return promotion

        promotion = queryset.filter(code1c=identifier).first()
        if promotion:
            return promotion
        raise NotFound("Акция не найдена.")

    def perform_create(self, serializer):
        self._check_counterparty_access(serializer.validated_data.get("counterparty"))
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        counterparty = serializer.validated_data.get("counterparty", serializer.instance.counterparty)
        self._check_counterparty_access(counterparty)
        serializer.save()

    def _check_counterparty_access(self, counterparty):
        if self.request.user.is_employee:
            return
        if counterparty and counterparty.contact_persons.filter(pk=self.request.user.pk).exists():
            return
        raise PermissionDenied("Недостаточно прав для работы с акцией этого контрагента.")
