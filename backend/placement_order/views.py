# views.py

from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
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
        ).prefetch_related(
            "items__nomenclature",
            "items__responsible"
        )

    def perform_create(self, serializer):
        nomenclatures = serializer.validated_data.pop("nomenclatures")

        order = serializer.save(owner=self.request.user)

        # Для каждого места берём responsible_ad и пишем в PlacementOrderItem
        PlacementOrderItem.objects.bulk_create([
            PlacementOrderItem(
                order=order,
                nomenclature=nom,
                responsible=nom.responsible_ad  # ← берётся автоматически
            )
            for nom in nomenclatures
        ])