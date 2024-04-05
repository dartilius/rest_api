from django.contrib import admin
from django.urls import include, path

from docs.views import docs, openapi

urlpatterns = [
    path('admin/', admin.site.urls),
    path('docs/', docs),
    path('docs/openapi-schema.yml', openapi),
    path('api/', include('nomenclatures.urls')),
    path('api/', include('users.urls')),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path("__debug__/", include("debug_toolbar.urls")),
]
