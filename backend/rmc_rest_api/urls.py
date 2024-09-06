from django.contrib import admin
from django.urls import include, path, re_path

from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from rest_framework import permissions

from users.views import logout
from docs.views import docs, openapi_scheme


urlpatterns = [
    path('admin/', admin.site.urls),
    path('docs/', docs),
    path('docs/openapi-schema.yml', openapi_scheme),
    path('api/', include('nomenclatures.urls')),
    path('api/', include('users.urls')),
    path('api/', include('files.urls')),
    path('api/', include('orders.urls')),
    path('api/', include('tasks.urls')),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('auth/logout/', logout, name='logout'),
    path('__debug__/', include('debug_toolbar.urls')),
]

schema_view = get_schema_view(
   openapi.Info(
       title='RMC REST API',
       default_version='v1',
       description='Документация ололо трололо',
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns += [
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=5),
            name='schema-redoc'),
]
