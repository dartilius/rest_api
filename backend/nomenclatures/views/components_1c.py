"""Nested 1C endpoints for nomenclature components."""

from rest_framework import viewsets
from rest_framework.exceptions import NotFound

from nomenclatures.models import DiscountRule, Nomenclature, NomenclatureMedia, NomenclatureTenant, TypeOfPlace
from nomenclatures.serializers_components_1c import DiscountRule1CSerializer, NomenclatureMedia1CSerializer, NomenclatureTenant1CSerializer, TypeOfPlace1CSerializer
from users.permissions import StaffCUDallRead


class OneCModelViewSet(viewsets.ModelViewSet):
    permission_classes = [StaffCUDallRead]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    lookup_value_regex = r"[0-9a-fA-F-]{36}"


class TypeOfPlace1CViewSet(OneCModelViewSet):
    queryset = TypeOfPlace.objects.all()
    serializer_class = TypeOfPlace1CSerializer


class NestedNomenclatureOneCViewSet(OneCModelViewSet):
    def get_nomenclature(self):
        try:
            return Nomenclature.objects.get(pk=self.kwargs["nomenclature_pk"])
        except Nomenclature.DoesNotExist as error:
            raise NotFound("Nomenclature not found.") from error


class NomenclatureTenant1CViewSet(NestedNomenclatureOneCViewSet):
    serializer_class = NomenclatureTenant1CSerializer
    lookup_field = "public_id"

    def get_queryset(self):
        return NomenclatureTenant.objects.filter(nomenclature=self.get_nomenclature())

    def perform_create(self, serializer):
        serializer.save(nomenclature=self.get_nomenclature())


class DiscountRule1CViewSet(NestedNomenclatureOneCViewSet):
    serializer_class = DiscountRule1CSerializer
    lookup_field = "public_id"

    def get_queryset(self):
        return DiscountRule.objects.filter(nomenclature=self.get_nomenclature())

    def perform_create(self, serializer):
        serializer.save(nomenclature=self.get_nomenclature())


class NomenclatureMedia1CViewSet(NestedNomenclatureOneCViewSet):
    serializer_class = NomenclatureMedia1CSerializer

    def get_queryset(self):
        return NomenclatureMedia.objects.filter(nomenclature=self.get_nomenclature())

    def perform_create(self, serializer):
        serializer.save(nomenclature=self.get_nomenclature())
