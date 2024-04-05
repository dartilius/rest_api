from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from nomenclatures.serializers import (
    NomenclatureSerializer,
    HardWareInfoSerializer,
    SettingsSerializer,
    NomenclatureGroupSerializer
)
from nomenclatures.models import Nomenclature, HardWareInfo, NomenclatureGroup
from users.permissions import AuthAndOnlySuperUserDelete


class NomenclatureViewSet(viewsets.ModelViewSet):
    """Работа с номенклатурами."""

    queryset = Nomenclature.objects.filter(
        is_active=True
    ).select_related('owner').prefetch_related('settings')
    serializer_class = NomenclatureSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [AuthAndOnlySuperUserDelete, ]

    def perform_create(self, serializer):
        nomenclature = serializer.save(owner=self.request.user)
        group = NomenclatureGroup.objects.create(
            owner=self.request.user,
            name=nomenclature.name,
            description=nomenclature.name
        )
        group.clients.add(nomenclature)
        group.save()


class HardWareInfoViewSet(viewsets.ModelViewSet):
    """Работа с информацией о железе разбы."""

    serializer_class = HardWareInfoSerializer

    def get_queryset(self):
        nomenclature_id = self.kwargs.get('nomenclature_id')
        return HardWareInfo.objects.filter(
            client__id=nomenclature_id
        ).select_related(
            'client', 'client__owner'
        ).prefetch_related('client__settings')


class SettingsViewSet(viewsets.ModelViewSet):
    """Работа с настройками номенклатуры."""

    serializer_class = SettingsSerializer

    def get_queryset(self):
        nomenclature_id = self.kwargs.get('nomenclature_id')
        return get_object_or_404(
            Nomenclature.objects.prefetch_related('settings'),
            id=nomenclature_id
        ).settings
        # return nomenclature.settings


class NomenclatureGroupSerializerViewSet(viewsets.ModelViewSet):
    """Работа с группами номенклатур."""

    serializer_class = NomenclatureGroupSerializer
    queryset = NomenclatureGroup.objects.all()
