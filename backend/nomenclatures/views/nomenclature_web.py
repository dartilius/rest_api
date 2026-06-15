from drf_spectacular.utils import extend_schema
from nomenclatures.models import Nomenclature
from nomenclatures.serializers import NomenclatureWebSerializer
from rest_framework import viewsets
from uuid import UUID
from rest_framework.exceptions import NotFound

@extend_schema(tags=["Номенклатуры WEB"])
class NomenclatureWebViewSet(viewsets.ModelViewSet):
    queryset = Nomenclature.web.all()
    serializer_class = NomenclatureWebSerializer

    def get_object(self):
        identifier = self.kwargs.get('pk')
        if not identifier:
            raise NotFound("Не указан идентификатор номенклатуры.")

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
                nomenclature = Nomenclature.objects.get(id=identifier)
                return nomenclature
            except Nomenclature.web.DoesNotExist:
                raise NotFound("Номенклатура не найдена.")

        # Если не UUID — ищем по old_catalog_slug
        try:
            nomenclature = Nomenclature.objects.get(old_catalog_slug=identifier)
            return nomenclature
        except Nomenclature.web.DoesNotExist:
            raise NotFound("Номенклатура не найдена.")