from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import BroadcastDemo, BroadcastDemoAsset


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
