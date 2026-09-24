"""1C CRUD endpoint for counterparties."""

from rest_framework import viewsets

from counterparties.models import Counterparty
from counterparties.serializers_1c import Counterparty1CSerializer
from users.permissions import StaffCUDallRead


class Counterparty1CViewSet(viewsets.ModelViewSet):
    queryset = Counterparty.objects.all()
    serializer_class = Counterparty1CSerializer
    permission_classes = [StaffCUDallRead]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    lookup_value_regex = r"[0-9a-fA-F-]{36}"

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
