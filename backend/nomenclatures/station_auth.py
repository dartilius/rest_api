"""Изолированная аутентификация endpoint-ов Content Player v2."""

from __future__ import annotations

from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from nomenclatures.models import StationCredential, StationInstallation
from nomenclatures.station_credentials import hash_station_token


class StationTokenAuthentication(BaseAuthentication):
    keyword = "Station"

    def authenticate_header(self, request):
        return self.keyword

    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme != self.keyword or not token or " " in token:
            raise AuthenticationFailed("Требуется station token.")
        token_hash = hash_station_token(token)
        credential = (
            StationInstallation.objects.select_related("nomenclature")
            .filter(token_hash=token_hash, is_active=True)
            .first()
        )
        if credential is None:
            credential = (
                StationCredential.objects.select_related("nomenclature")
                .filter(token_hash=token_hash, is_active=True)
                .first()
            )
        if credential is None:
            raise AuthenticationFailed("Token станции недействителен.")
        # Станция не является Django-пользователем и не получает права JWT-пользователя.
        return AnonymousUser(), credential
