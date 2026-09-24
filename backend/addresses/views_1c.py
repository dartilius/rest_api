"""1C CRUD endpoint for addresses."""

from rest_framework import viewsets

from addresses.models import Address
from addresses.serializers_1c import Address1CSerializer
from users.permissions import StaffCUDallRead


class Address1CViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = Address1CSerializer
    permission_classes = [StaffCUDallRead]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    lookup_value_regex = r"[0-9a-fA-F-]{36}"
