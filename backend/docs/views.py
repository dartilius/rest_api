from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from drf_spectacular.renderers import OpenApiYamlRenderer
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView


docs = SpectacularRedocView.as_view(url_name="schema")
openapi_scheme = SpectacularAPIView.as_view(renderer_classes=[OpenApiYamlRenderer])


def integration_guide(request):
    """Serve the versioned integration guide shipped with this backend."""
    guide = Path(settings.BASE_DIR) / "docs" / "ONE_C_API_GUIDE.md"
    return HttpResponse(guide.read_text(encoding="utf-8"), content_type="text/markdown; charset=utf-8")
