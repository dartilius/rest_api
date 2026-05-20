from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, inline_serializer
from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from api.constants import get_instance_or_404
from users.permissions import StaffCUDallRead
from ..models import DiscountRule, Nomenclature
from ..serializers import DiscountRuleSerializer


@extend_schema(tags=["Номенклатуры - Скидки"])
class DiscountRuleViewSet(viewsets.ModelViewSet):
    """
    Правила скидок для конкретной номенклатуры.

    Маршруты (nested под номенклатурой):
        GET    /api/nomenclatures/{nomenclature_pk}/discounts/
        POST   /api/nomenclatures/{nomenclature_pk}/discounts/
        GET    /api/nomenclatures/{nomenclature_pk}/discounts/{id}/
        PATCH  /api/nomenclatures/{nomenclature_pk}/discounts/{id}/
        DELETE /api/nomenclatures/{nomenclature_pk}/discounts/{id}/
        GET    /api/nomenclatures/{nomenclature_pk}/discounts/calculate/?days=35
    """

    serializer_class = DiscountRuleSerializer
    permission_classes = [StaffCUDallRead]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def _get_nomenclature(self):
        nomenclature_pk = self.kwargs.get("nomenclature_pk")
        return get_instance_or_404(Nomenclature, nomenclature_pk)

    def get_queryset(self):
        return DiscountRule.objects.filter(
            nomenclature_id=self.kwargs["nomenclature_pk"]
        ).order_by("days_from")

    def perform_create(self, serializer):
        nomenclature = self._get_nomenclature()
        serializer.save(nomenclature=nomenclature)

    @extend_schema(
        summary="Рассчитать коэффициент скидки",
        parameters=[
            OpenApiParameter(
                name="days",
                description="Кол-во дней размещения",
                required=True,
                type=int,
            )
        ],
        responses={
            200: inline_serializer(
                name="DiscountCalculateResponse",
                fields={
                    "days": serializers.IntegerField(),
                    "coefficient": serializers.DecimalField(max_digits=4, decimal_places=3),
                    "base_price": serializers.DecimalField(max_digits=10, decimal_places=2),
                    "final_price": serializers.DecimalField(max_digits=10, decimal_places=2),
                },
            ),
            400: OpenApiResponse(description="Не передан параметр days"),
        },
    )
    @action(detail=False, methods=["get"])
    def calculate(self, request, **kwargs):
        """
        Рассчитать итоговую цену с учётом скидки.

        GET /api/nomenclatures/{nomenclature_pk}/discounts/calculate/?days=35
        """
        days_raw = request.query_params.get("days")
        if not days_raw:
            raise ValidationError({"days": "Обязательный параметр."})

        try:
            days = int(days_raw)
            if days <= 0:
                raise ValueError
        except ValueError:
            raise ValidationError({"days": "Должно быть положительным целым числом."})

        nomenclature = self._get_nomenclature()
        coefficient = DiscountRule.get_coefficient(nomenclature.id, days)
        base_price = nomenclature.pricePerMonth
        final_price = base_price * coefficient

        return Response({
            "days": days,
            "coefficient": coefficient,
            "base_price": base_price,
            "final_price": final_price,
        })