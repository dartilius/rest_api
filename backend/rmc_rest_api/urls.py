from django.contrib import admin
from django.urls import include, path, re_path
from django.http import HttpResponse  # 👈 ДОБАВИТЬ
from django.conf import settings  # 👈 ДОБАВИТЬ

from drf_spectacular.views import (
    SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
)
from rest_framework import permissions

from docs.views import docs, openapi_scheme
from users.views import LogoutView

# 👇 ДОБАВИТЬ ЭТУ ФУНКЦИЮ (для просмотра истории запросов)
def debug_toolbar_panel(request):
    """Страница-заглушка для просмотра истории Django Debug Toolbar"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Debug Toolbar - RMC API</title>
        <meta charset="utf-8">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                margin: 0;
            }
            .container {
                max-width: 800px;
                margin: 50px auto;
                background: white;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            }
            h1 { 
                color: #333; 
                margin-top: 0;
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
            }
            .info { 
                background: #e3f2fd; 
                padding: 15px; 
                border-radius: 8px; 
                margin: 20px 0;
                border-left: 4px solid #2196f3;
            }
            .step {
                background: #f5f5f5;
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
                font-family: monospace;
            }
            code {
                background: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: monospace;
                color: #d63384;
            }
            .badge {
                display: inline-block;
                background: #28a745;
                color: white;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 12px;
                margin-right: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔧 Django Debug Toolbar</h1>
            <p>Панель отладки активна и готова к работе!</p>
            
            <div class="info">
                <strong>✅ Как посмотреть SQL запросы и отладку API:</strong>
                <div class="step">
                    <span class="badge">1</span> Нажмите на иконку <strong>«DjDT»</strong> или шестеренку <strong>⚙️</strong> справа
                </div>
                <div class="step">
                    <span class="badge">2</span> В открывшейся панели выберите пункт <strong>«History» (История)</strong>
                </div>
                <div class="step">
                    <span class="badge">3</span> Выберите любой API или админ запрос из списка
                </div>
                <div class="step">
                    <span class="badge">4</span> Откройте панель <strong>«SQL»</strong> — увидите все запросы к БД
                </div>
            </div>
            
            <p><strong>💡 Советы:</strong></p>
            <ul>
                <li>Если панель не видна, убедитесь что <code>DEBUG=True</code> в настройках</li>
                <li>Панель появляется на HTML страницах (<code>/admin/</code>, <code>/debug-panel/</code>)</li>
                <li>API запросы (JSON) смотрите через вкладку <strong>«History»</strong></li>
                <li>Для лучшей совместимости используйте <code>http://localhost:8000</code> вместо IP адреса</li>
            </ul>
            
            <hr>
            <p style="text-align: center; color: #666; font-size: 12px;">
                Django Debug Toolbar — отладка SQL, кеша, шаблонов и запросов
            </p>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)


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

    path('api/', include('feedback.urls')),

    path('api/', include('users.urls')),
    path('api/', include('files.urls')),
    path('api/', include('orders.urls')),
    path('api/', include('tasks.urls')),
    path("api/", include("placement_order.urls")),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('__debug__/', include('debug_toolbar.urls')),
]

# 👇 ДОБАВИТЬ ЭТОТ БЛОК (добавляем URL для просмотра панели только в DEBUG режиме)
if settings.DEBUG:
    urlpatterns += [
        path('debug-panel/', debug_toolbar_panel, name='debug_panel'),
    ]


# from django.contrib import admin
# from django.urls import include, path, re_path

# from drf_spectacular.views import (
#     SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
# )
# from rest_framework import permissions

# from docs.views import docs, openapi_scheme
# from users.views import LogoutView

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('docs/', docs),
#     path('docs/openapi-schema.yml', openapi_scheme),
#     path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
#     path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
#     path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
#     path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
#     path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
#     path('api/', include('addresses.urls')),
#     path('api/', include('nomenclatures.urls')),
#     path('api/', include('counterparties.urls')),

#     path('api/', include('promotions.urls')),

#     path('api/', include('brands.urls')),

#     path('api/', include('feedback.urls')),

#     path('api/', include('users.urls')),
#     path('api/', include('files.urls')),
#     path('api/', include('orders.urls')),
#     path('api/', include('tasks.urls')),
#     path("api/", include("placement_order.urls")),
#     path('auth/', include('djoser.urls')),
#     path('auth/', include('djoser.urls.jwt')),
#     path('logout/', LogoutView.as_view(), name='logout'),
#     path('__debug__/', include('debug_toolbar.urls')),
# ]
