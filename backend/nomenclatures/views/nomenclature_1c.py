"""Inbound 1C API for nomenclatures."""

from rest_framework import status, viewsets
from rest_framework.response import Response

from nomenclatures.models import Nomenclature
from nomenclatures.serializers_1c import (
    Nomenclature1CReadSerializer,
    Nomenclature1CWriteSerializer,
)
from users.permissions import StaffCUDallRead


class Nomenclature1CViewSet(viewsets.ModelViewSet):
    """CRUD endpoint used by 1C; records are addressed exclusively by UUID."""

    queryset = Nomenclature.objects.all()
    permission_classes = [StaffCUDallRead]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    lookup_value_regex = (
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    )

    def get_queryset(self):
        return self.queryset

    def get_serializer_class(self):
        if self.action in {"list", "retrieve"}:
            return Nomenclature1CReadSerializer
        return Nomenclature1CWriteSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        return Response({"id": str(serializer.instance.id)}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"id": str(serializer.instance.id)})
