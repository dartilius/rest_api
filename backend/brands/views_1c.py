"""1C CRUD endpoint for brands."""

from rest_framework import viewsets

from brands.models import Brand
from brands.serializers_1c import Brand1CSerializer
from users.permissions import StaffCUDallRead


class Brand1CViewSet(viewsets.ModelViewSet):
    queryset = Brand.all_objects.all()
    serializer_class = Brand1CSerializer
    permission_classes = [StaffCUDallRead]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    lookup_value_regex = r"[0-9a-fA-F-]{36}"
