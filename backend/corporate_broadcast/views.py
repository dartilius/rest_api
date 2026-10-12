from django.db.models import Prefetch, Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, serializers, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.settings import APISettings, DEFAULTS

from .constants import DEMO_FORMAT_CHOICES, MEDIA_RULES
from .models import BroadcastDemo, BroadcastDemoAsset
from .serializers import BroadcastDemoSerializer


def valid_asset_query():
    query = Q(pk__in=[])
    for role, (types, extensions) in MEDIA_RULES.items():
        suffixes = Q(pk__in=[])
        for extension in extensions:
            suffixes |= Q(file__source__iendswith=extension)
        query |= Q(role=role, file__type__in=types) & suffixes
    return Q(file__is_active=True) & query


class DemoContentNegotiation(DefaultContentNegotiation):
    # `format` is a domain filter here, not DRF's renderer override.
    settings = APISettings({"URL_FORMAT_OVERRIDE": None}, DEFAULTS)


@extend_schema(tags=["Демо корпоративного вещания"], parameters=[OpenApiParameter("format", str, enum=[key for key, _ in DEMO_FORMAT_CHOICES])])
class BroadcastDemoViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    content_negotiation_class = DemoContentNegotiation
    queryset = BroadcastDemo.objects.none()
    serializer_class = BroadcastDemoSerializer
    permission_classes = (AllowAny,)
    # Public previews must work even with an expired session token.
    authentication_classes = ()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset
        selected = self.request.query_params.get("format")
        if selected is not None and selected not in dict(DEMO_FORMAT_CHOICES):
            raise serializers.ValidationError({"format": "Неизвестный формат / сценарий."})
        assets = BroadcastDemoAsset.objects.filter(valid_asset_query()).select_related("file")
        queryset = BroadcastDemo.objects.filter(is_published=True, assets__in=assets.exclude(role="poster")).distinct().prefetch_related(Prefetch("assets", queryset=assets))
        if selected:
            queryset = queryset.filter(format=selected)
        return queryset

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        return response
