from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework import viewsets
from brands.filters import BrandFilter
from brands.models import Brand
from brands.serializers import BrandCreateSerializer, BrandSerializer, BrandShortSerializer
from uuid import UUID


class BrandViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ["get", "post", "patch", "delete"]
    queryset = Brand.all_objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = BrandFilter

    def get_serializer_class(self):
        if self.action == "create":
            return BrandCreateSerializer
        return BrandSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        brand = serializer.save()
        short = BrandShortSerializer(brand)
        return Response(short.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Мягкое удаление бренда."""

        brand = self.get_object()
        brand.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_object(self):
        """
        Получаем бренд по UUID или code1c.
        """
        identifier = self.kwargs.get(self.lookup_field, None)
        if not identifier:
            raise NotFound("Не указан идентификатор бренда.")

        # пробуем UUID
        try:
            uuid_obj = UUID(str(identifier))
            return Brand.all_objects.get(id=uuid_obj)
        except (ValueError, Brand.DoesNotExist):
            pass

        # пробуем code1c
        try:
            return Brand.all_objects.get(code1c=identifier)
        except Brand.DoesNotExist:
            raise NotFound("Бренд не найден.")
