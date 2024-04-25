from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from nomenclatures.serializers import (
    NomenclatureSerializer,
    HardWareInfoSerializer,
    SettingsSerializer,
    NomenclatureGroupSerializer, NomenclatureListSerializer
)
from nomenclatures.models import (
    Nomenclature,
    HardWareInfo,
    NomenclatureGroup
)
from users.models import User
from users.permissions import AuthAndOnlySuperUserDelete


class NomenclatureViewSet(viewsets.ModelViewSet):
    """Работа с номенклатурами."""

    queryset = Nomenclature.objects.filter(
        is_active=True
    ).select_related('owner').prefetch_related('settings')
    pagination_class = LimitOffsetPagination
    # permission_classes = [AuthAndOnlySuperUserDelete, ]

    def get_serializer(self, *args, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        nomenclature = serializer.save(owner=User.objects.get(pk=1))
        group = NomenclatureGroup.objects.create(
            owner=self.request.user,
            name=nomenclature.name,
            description=nomenclature.name,
            settings=settings
        )
        group.clients.add(nomenclature)
        group.save()

    def get_serializer(self, *args, **kwargs):
        if self.request.method == 'GET' and not kwargs['detail']:
            serializer = NomenclatureListSerializer
        else:
            serializer = NomenclatureSerializer
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return serializer(*args, **kwargs)


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
            Nomenclature.objects,
            id=nomenclature_id
        ).settings


class NomenclatureGroupViewSet(viewsets.ModelViewSet):
    """Работа с группами номенклатур."""

    serializer_class = NomenclatureGroupSerializer
    pagination_class = LimitOffsetPagination
    queryset = NomenclatureGroup.objects.all().prefetch_related(
        'clients', 'clients__settings'
    ).select_related('owner')
