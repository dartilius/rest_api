"""Показывает отладочную панель только сотрудникам внутри Django admin."""

from django.conf import settings
from django.urls import Resolver404, resolve


def show_toolbar(request):
    if not settings.DEBUG:
        return False
    user = getattr(request, "user", None)
    if not user or not user.is_active or not user.is_staff:
        return False
    try:
        namespaces = resolve(request.path_info).namespaces
    except Resolver404:
        return False
    # djdt нужен для загрузки содержимого вкладок уже открытой панели.
    return "admin" in namespaces or "djdt" in namespaces
