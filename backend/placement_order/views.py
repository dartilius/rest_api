# views.py

from django.db import transaction
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from services.api_1c_client import logger
from .models import PlacementOrder, PlacementOrderItem
from .serializers import CommercialStatusSerializer, PlacementOrderSerializer


MARKETING_ROLES = {"manager", "admin", "superuser"}


class MarketingReportPermission(BasePermission):
    message = "Marketing report is available to managers and marketing staff only."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in MARKETING_ROLES
        )


class PlacementOrderViewSet(mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    serializer_class = PlacementOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PlacementOrder.objects.select_related("owner").prefetch_related("items")
        if getattr(self.request.user, "role", None) in MARKETING_ROLES:
            return queryset
        return queryset.filter(owner=self.request.user)

    def get_serializer_class(self):
        if self.action == "commercial_status":
            return CommercialStatusSerializer
        return PlacementOrderSerializer

    @action(detail=True, methods=["patch"], url_path="commercial-status")
    def commercial_status(self, request, *args, **kwargs):
        if getattr(request.user, "role", None) not in MARKETING_ROLES:
            return Response(
                {"detail": "Only managers and marketing staff may change commercial status."},
                status=status.HTTP_403_FORBIDDEN,
            )
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def perform_create(self, serializer):
        nomenclatures = serializer.validated_data.pop("nomenclatures")
        with transaction.atomic():
            order = serializer.save(owner=self.request.user)
            PlacementOrderItem.objects.bulk_create([
                PlacementOrderItem(
                    order=order,
                    nomenclature=nom,
                    responsible=nom.responsible_ad,
                )
                for nom in nomenclatures
            ])

        try:
            from placement_order.tasks import send_placement_order_email
            send_placement_order_email.delay(order_id=str(order.id))
        except Exception as e:
            logger.warning(f"Не удалось запустить таск письма: {e}")

        # try:
        #     payload = {
        #         "duration": order.duration,
        #         "all_days": order.all_days,
        #         "days_of_week": order.days_of_week,
        #         "owner": order.owner.code1c,
        #         "items": [
        #             {
        #                 "nomenclature": item.nomenclature.code1c,
        #                 "responsible": item.responsible.code1c if item.responsible else None,
        #             }
        #             for item in order.items.select_related("nomenclature", "responsible").all()
        #         ]
        #     }
            # response = api_1c.post("/CreatePlacementOrder", payload)
            # response.raise_for_status()
            # code1c = response.json().get("code1c")
            # if code1c:
            #     order.code1c = code1c
            #     order.save(update_fields=["code1c"])
            # else:
            #     logger.warning("PlacementOrder %s создан без code1c", order.id)
        # except Exception as e:
        #     logger.warning("Не удалось отправить PlacementOrder в 1С: %s", e)
