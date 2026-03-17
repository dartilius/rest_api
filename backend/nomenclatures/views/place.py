from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from nomenclatures.models import TypeOfPlace
from nomenclatures.serializers import TypeOfPlaceSerializer
from users.permissions import StaffCUDallRead

@extend_schema(tags=["Номенклатуры - Тип места"])
class TypeOfPlaceViewSet(viewsets.ModelViewSet):
    queryset = TypeOfPlace.objects.all()
    serializer_class = TypeOfPlaceSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [StaffCUDallRead()]