from django.contrib import admin
from django.urls import include, path, re_path

from drf_spectacular.views import (
    SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
)
from rest_framework import permissions

from docs.views import docs, openapi_scheme
from users.views import LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('docs/', docs),
    path('docs/openapi-schema.yml', openapi_scheme),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/', include('addresses.urls')),
    path('api/', include('nomenclatures.urls')),
    path('api/', include('counterparties.urls')),

    path('api/', include('promotions.urls')),

    path('api/', include('brands.urls')),

    path('api/', include('users.urls')),
    path('api/', include('files.urls')),
    path('api/', include('orders.urls')),
    path('api/', include('tasks.urls')),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('__debug__/', include('debug_toolbar.urls')),
]
