from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from django.urls import reverse

from .models import BroadcastDemo, BroadcastDemoAsset, BroadcastLanding, TypesOfPlaceBroadcast, TypeOfFormats
from brands.models import Brand

class DemoAssetSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = BroadcastDemoAsset
        fields = ("id", "role", "caption", "sort_order", "url", "duration_seconds")

    @extend_schema_field(serializers.URLField())
    def get_url(self, obj):
        return obj.file.url

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_duration_seconds(self, obj):
        length = obj.file.length
        if length is None:
            return None
        return length.hour * 3600 + length.minute * 60 + length.second + length.microsecond / 1000000


class BroadcastDemoSerializer(serializers.ModelSerializer):
    assets = serializers.SerializerMethodField()

    class Meta:
        model = BroadcastDemo
        fields = ("id", "title", "format", "description", "transcript", "sort_order", "assets")

    @extend_schema_field(DemoAssetSerializer(many=True))
    def get_assets(self, obj):
        return DemoAssetSerializer([asset for asset in obj.assets.all() if asset.is_playable], many=True).data


class BroadcastDemoListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BroadcastDemo
        fields = ("id", "title", "format", "description", "sort_order")

class TypeOfFormatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeOfFormats
        fields = ("id", "format_type", "description", "demo")

class TypesOfPlaceBroadcastSerializer(serializers.ModelSerializer):
    format_label = serializers.CharField(source="get_format_type_display", read_only=True)

    class Meta:
        model = TypesOfPlaceBroadcast
        fields = ("id", "title", "type_of_place", "format_type", "format_label", "description")


class LandingBrandSerializer(serializers.ModelSerializer):
    logotype = serializers.SerializerMethodField()

    @extend_schema_field(serializers.URLField())
    def get_logotype(self, obj):
        if not obj.logotype:
            return None
        # Cache a stable endpoint, not an expiring MinIO signature.
        path = reverse("broadcast-landing-brand-logo", kwargs={
            "pk": self.context["landing_id"], "brand_id": obj.pk,
        })
        request = self.context.get("request")
        return request.build_absolute_uri(path) if request else path

    class Meta:
        model = Brand
        fields = ("id", "name", "logotype")


class BroadcastLandingSerializer(serializers.ModelSerializer):
    logo_brands = serializers.SerializerMethodField()
    format_type = serializers.SerializerMethodField()
    demo = serializers.SerializerMethodField()

    @extend_schema_field(LandingBrandSerializer(many=True))
    def get_logo_brands(self, obj):
        return LandingBrandSerializer(obj.public_brands, many=True, context={
            **self.context, "landing_id": obj.pk,
        }).data

    @extend_schema_field(TypesOfPlaceBroadcastSerializer(allow_null=True))
    def get_format_type(self, obj):
        if not obj.format_type or not obj.format_type.is_active:
            return None
        return TypesOfPlaceBroadcastSerializer(obj.format_type).data

    @extend_schema_field(serializers.UUIDField(allow_null=True))
    def get_demo(self, obj):
        return obj.demo_id if obj.demo and obj.demo.is_published else None

    class Meta:
        model = BroadcastLanding
        fields = ("id", "title", "description", "logo_brands", "format_type", "demo")
