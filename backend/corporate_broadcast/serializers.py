from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

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
    class Meta:
        model = TypesOfPlaceBroadcast
        fields = ("id", "type_of_place", "format_type", "description")


class LandingBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ("id", "name", "logotype")


class BroadcastLandingSerializer(serializers.ModelSerializer):
    logo_brands = LandingBrandSerializer(many=True, read_only=True)

    class Meta:
        model = BroadcastLanding
        fields = "__all__"
