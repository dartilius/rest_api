from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from nomenclatures.models import TypeOfPlace
from nomenclatures.serializers import TypeOfPlaceSerializer
from users.permissions import StaffCUDallRead
from uuid import UUID
from rest_framework.exceptions import NotFound
@extend_schema(tags=["Номенклатуры - Тип места"])
class TypeOfPlaceViewSet(viewsets.ModelViewSet):
    queryset = TypeOfPlace.objects.all()
    serializer_class = TypeOfPlaceSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [StaffCUDallRead()]

    def get_object(self):
        identifier = self.kwargs.get('pk')
        if not identifier:
            raise NotFound("Не указан идентификатор Типа места.")

        # Проверяем, валидный ли UUID
        is_uuid = False
        try:
            UUID(str(identifier))
            is_uuid = True
        except ValueError:
            is_uuid = False

        # Если UUID — ищем по id
        if is_uuid:
            try:
                type_of_place = TypeOfPlace.objects.get(id=identifier)
                return type_of_place
            except TypeOfPlace.DoesNotExist:
                raise NotFound("Номенклатура не найдена.")

        # Если не UUID — ищем по code1c
        try:
            type_of_place = TypeOfPlace.objects.get(code1c=identifier)
            return type_of_place
        except TypeOfPlace.DoesNotExist:
            raise NotFound("Номенклатура не найдена.")