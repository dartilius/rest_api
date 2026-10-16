"""Изолированная аутентификация endpoint-ов Content Player v2."""

from __future__ import annotations

from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission
from drf_spectacular.extensions import OpenApiAuthenticationExtension

from nomenclatures.models import StationCredential, StationInstallation
from nomenclatures.player_v2.credentials import hash_station_token
from nomenclatures.player_v2.recovery import (
    InvalidRecoveryToken,
    RecoveryClaims,
    decode_recovery_token,
)


def lookup_station_token(token):
    token_hash = hash_station_token(token)
    credential = StationInstallation.objects.select_related("nomenclature").filter(
        token_hash=token_hash, is_active=True,
    ).first()
    if credential is None:
        credential = StationCredential.objects.select_related("nomenclature").filter(
            token_hash=token_hash, is_active=True,
        ).first()
    return credential


class StationTokenAuthentication(BaseAuthentication):
    keyword = "Station"

    def authenticate_header(self, request):
        return self.keyword

    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme != self.keyword or not token or " " in token:
            raise AuthenticationFailed("Требуется station token.")
        credential = lookup_station_token(token)
        if credential is None:
            raise AuthenticationFailed("Token станции недействителен.")
        # Станция не является Django-пользователем и не получает права JWT-пользователя.
        return AnonymousUser(), credential


class StationTokenSchema(OpenApiAuthenticationExtension):
    target_class = StationTokenAuthentication
    name = "StationToken"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey", "in": "header", "name": "Authorization",
            "description": "Ключ установки плеера: Station <token>. JWT пользователя здесь не применяется.",
        }


class StationRecoveryAuthentication(BaseAuthentication):
    """Проверить подписанный ключ восстановления установки без JWT."""

    keyword = "StationRecovery"

    def authenticate_header(self, request):
        return self.keyword

    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme != self.keyword or not token or " " in token:
            raise AuthenticationFailed("Требуется ключ восстановления станции.")
        try:
            claims = decode_recovery_token(token)
        except InvalidRecoveryToken as exc:
            raise AuthenticationFailed("Ключ восстановления станции недействителен.") from exc
        return AnonymousUser(), claims


class HasActiveStationInstallation(BasePermission):
    """Разрешить выдачу recovery-ключа только активной установке v2."""

    def has_permission(self, request, view):
        return isinstance(request.auth, StationInstallation) and request.auth.is_active


class HasStationRecoveryClaims(BasePermission):
    """Разрешить восстановление только после строгой проверки утверждений."""

    def has_permission(self, request, view):
        return isinstance(request.auth, RecoveryClaims)


class StationRecoverySchema(OpenApiAuthenticationExtension):
    target_class = StationRecoveryAuthentication
    name = "StationRecoveryToken"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey", "in": "header", "name": "Authorization",
            "description": "Ключ восстановления установки: StationRecovery <token>. JWT не применяется.",
        }
