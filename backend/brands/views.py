from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from brands.models import Brand
from brands.serializers import BrandCreateSerializer, BrandSerializer, BrandShortSerializer
from orders.views import NoDeleteViewSet


class BrandViewSet(NoDeleteViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        queryset = Brand.all_objects.all()  # берём все бренды, включая мягко удалённые
        is_deleted = self.request.query_params.get("is_deleted")
        if is_deleted is not None:
            if is_deleted.lower() in ["true", "1"]:
                queryset = queryset.filter(is_deleted=True)
            elif is_deleted.lower() in ["false", "0"]:
                queryset = queryset.filter(is_deleted=False)
            else:
                queryset = queryset.filter(
                    is_deleted=False)  # по умолчанию только активные
        return queryset

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
