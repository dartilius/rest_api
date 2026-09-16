# views.py

from django.db import transaction
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from services.api_1c_client import logger
from .models import PlacementOrder, PlacementOrderItem
from .serializers import CommercialStatusSerializer, PlacementOrderSerializer


MARKETING_ROLES = {"manager", "admin", "superuser"}


def is_staff_member(user):
    return bool(
        user and user.is_authenticated and (
            getattr(user, "role", None) in MARKETING_ROLES
            or getattr(user, "is_superuser", False)
        )
    )


class MarketingReportPermission(BasePermission):
    message = "Marketing report is available to managers and marketing staff only."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and is_staff_member(request.user)
        )


class PlacementOrderViewSet(mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.ListModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin,
                            viewsets.GenericViewSet):
    serializer_class = PlacementOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PlacementOrder.objects.select_related("owner").prefetch_related(
            "items__nomenclature", "items__responsible"
        )
        if not is_staff_member(self.request.user):
            return queryset.filter(owner=self.request.user)
        owner_id = self.request.query_params.get("owner_id")
        commercial_status = self.request.query_params.get("commercial_status")
        date_from = self.request.query_params.get("from")
        date_to = self.request.query_params.get("to")
        if owner_id:
            queryset = queryset.filter(owner_id=owner_id)
        if commercial_status:
            queryset = queryset.filter(commercial_status=commercial_status)
        if date_from:
            queryset = queryset.filter(created__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created__date__lte=date_to)
        return queryset

    def get_serializer_class(self):
        if self.action == "commercial_status":
            return CommercialStatusSerializer
        return PlacementOrderSerializer

    @action(detail=True, methods=["patch"], url_path="commercial-status")
    def commercial_status(self, request, *args, **kwargs):
        if not is_staff_member(request.user):
            return Response(
                {"detail": "Only managers and marketing staff may change commercial status."},
                status=status.HTTP_403_FORBIDDEN,
            )
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def _require_current_revision(self, request, order):
        value = request.headers.get("If-Match")
        if value is None:
            return Response({"detail": "If-Match header with the current revision is required."}, status=428)
        try:
            expected = int(value.strip('"'))
        except (TypeError, ValueError):
            return Response({"detail": "If-Match must be an integer revision."}, status=400)
        if expected != order.revision:
            return Response(self.get_serializer(order).data, status=status.HTTP_409_CONFLICT)
        return None

    @staticmethod
    def _may_edit_as_owner(request, order):
        return order.owner_id == request.user.id and order.commercial_status == "new"

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            order = self.get_object()
            order = PlacementOrder.objects.select_for_update().get(pk=order.pk)
            if not self._may_edit_as_owner(request, order):
                return Response({"detail": "Only the owner may edit a new media plan."}, status=403)
            revision_error = self._require_current_revision(request, order)
            if revision_error:
                return revision_error
            serializer = self.get_serializer(order, data=request.data, partial=kwargs.pop("partial", False))
            serializer.is_valid(raise_exception=True)
            nomenclatures = serializer.validated_data.pop("nomenclatures", None)
            updated = serializer.save(revision=order.revision + 1)
            if nomenclatures is not None:
                PlacementOrderItem.objects.filter(order=updated).delete()
                PlacementOrderItem.objects.bulk_create([
                    PlacementOrderItem(
                        order=updated,
                        nomenclature=nom,
                        responsible=nom.responsible_ad,
                    )
                    for nom in nomenclatures
                ])
        return Response(self.get_serializer(updated).data)

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            order = self.get_object()
            order = PlacementOrder.objects.select_for_update().get(pk=order.pk)
            if not self._may_edit_as_owner(request, order):
                return Response({"detail": "Only the owner may delete a new media plan."}, status=403)
            revision_error = self._require_current_revision(request, order)
            if revision_error:
                return revision_error
            order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def copy(self, request, *args, **kwargs):
        source = self.get_object()
        if source.owner_id != request.user.id:
            return Response({"detail": "Only the owner may copy a media plan."}, status=403)
        with transaction.atomic():
            order = PlacementOrder.objects.create(
                owner=request.user, duration=source.duration, start_date=source.start_date,
                end_date=source.end_date, all_days=source.all_days, days_of_week=source.days_of_week,
                attribution=source.attribution, name=f"Копия {source.name}"[:120],
            )
            PlacementOrderItem.objects.bulk_create([
                PlacementOrderItem(order=order, nomenclature=item.nomenclature, responsible=item.responsible)
                for item in source.items.select_related("nomenclature", "responsible")
            ])
        return Response(self.get_serializer(order).data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        nomenclatures = serializer.validated_data.pop("nomenclatures")
        with transaction.atomic():
            if not serializer.validated_data.get("name"):
                base_name = f"Медиаплан {timezone.localdate():%Y-%m-%d}"
                names = set(PlacementOrder.objects.filter(name__startswith=base_name).values_list("name", flat=True))
                name, number = base_name, 2
                while name in names:
                    name = f"{base_name} {number}"
                    number += 1
                serializer.validated_data["name"] = name
            order = serializer.save(owner=self.request.user)
            PlacementOrderItem.objects.bulk_create([
                PlacementOrderItem(
                    order=order,
                    nomenclature=nom,
                    responsible=nom.responsible_ad,
                )
                for nom in nomenclatures
            ])

        def enqueue_email():
            try:
                from placement_order.tasks import send_placement_order_email
                send_placement_order_email.delay(order_id=str(order.id))
            except Exception as exc:
                logger.warning("Could not enqueue placement-order email: %s", exc)

        transaction.on_commit(enqueue_email)
