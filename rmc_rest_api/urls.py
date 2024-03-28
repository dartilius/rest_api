from django.contrib import admin
from django.urls import path

from docs.views import docs, openapi

urlpatterns = [
    path('admin/', admin.site.urls),
    path('docs/', docs),
    path('docs/openapi-schema.yml', openapi)
]
