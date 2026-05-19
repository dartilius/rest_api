# views.py

from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from services.api_1c_client import api_1c, logger
from .models import PlacementOrder, PlacementOrderItem
from .serializers import PlacementOrderSerializer


class PlacementOrderViewSet(mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    serializer_class = PlacementOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PlacementOrder.objects.filter(
            owner=self.request.user
        )

    def perform_create(self, serializer):
        print("validated_data:", serializer.validated_data)
        nomenclatures = serializer.validated_data.pop("nomenclatures")
        order = serializer.save(owner=self.request.user)
        print("order.start_date:", order.start_date)
        print("order.end_date:", order.end_date)

        PlacementOrderItem.objects.bulk_create([
            PlacementOrderItem(
                order=order,
                nomenclature=nom,
                responsible=nom.responsible_ad
            )
            for nom in nomenclatures
        ])

        try:
            payload = {
                "duration": order.duration,
                "all_days": order.all_days,
                "days_of_week": order.days_of_week,
                "owner": order.owner.code1c,
                "items": [
                    {
                        "nomenclature": item.nomenclature.code1c,
                        "responsible": item.responsible.code1c if item.responsible else None,
                    }
                    for item in order.items.select_related("nomenclature", "responsible").all()
                ]
            }
            response = api_1c.post("/CreatePlacementOrder", payload)
            response.raise_for_status()
            code1c = response.json().get("code1c")
            if code1c:
                order.code1c = code1c
                order.save(update_fields=["code1c"])
            else:
                logger.warning("PlacementOrder %s создан без code1c", order.id)
        except Exception as e:
            logger.warning("Не удалось отправить PlacementOrder в 1С: %s", e)