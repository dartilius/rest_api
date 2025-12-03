from django.db.models import Q
from django.shortcuts import render
from rest_framework import viewsets

from counterparties.models import Counterparty
from promotions.models import Promotion
from promotions.serializers import PromotionSerializer, PromotionListSerializer
from users.models import CONTACT_PERSON_ROLES


class PromotionViewSet(viewsets.ModelViewSet):
    lookup_field = 'id_or_code1c'
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    queryset = Promotion.objects.all()

    def get_serializer(self, *args, **kwargs):
        if self.action == "list":
            serializer = PromotionListSerializer
        else:
            serializer = PromotionSerializer

        return serializer(*args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        is_admin = (
                user.is_admin
                or user.is_superuser
                or user.is_ordinary
                or user.is_manager
        )

        qs = Counterparty.objects.all().order_by('id')

        if user.role in CONTACT_PERSON_ROLES:
            user_counterparties = Counterparty.objects.filter(contact_person=user)
            qs = qs.filter(
                Q(id__in=user_counterparties.values_list('id', flat=True))
            ).distinct()
        elif is_admin:
            pass  # админы видят всех

        else:
            qs = Counterparty.objects.none()
        return qs
