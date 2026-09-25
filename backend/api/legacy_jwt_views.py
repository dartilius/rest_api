"""HTTP views that are deliberately kept outside DRF authentication imports."""

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.utils import datetime_from_epoch

from api.jwt import issue_token_pair, legacy_window_is_open


class LegacyTokenRefreshView(APIView):
    """Exchange one old HS256 refresh token for an RS256 access/refresh pair."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        if not legacy_window_is_open():
            raise AuthenticationFailed(_('Legacy JWT support has expired.'))

        raw_token = request.data.get('refresh')
        if not raw_token:
            raise AuthenticationFailed(_('Refresh token is required.'))

        try:
            payload = jwt.decode(
                raw_token,
                settings.JWT_LEGACY_HS256_SECRET,
                algorithms=['HS256'],
                options={'require': ['exp', 'jti', 'token_type', 'user_id']},
            )
        except jwt.PyJWTError as error:
            raise AuthenticationFailed(_('Invalid legacy refresh token.')) from error

        if payload.get('token_type') != 'refresh':
            raise AuthenticationFailed(_('Wrong token type.'))
        if BlacklistedToken.objects.filter(token__jti=payload['jti']).exists():
            raise AuthenticationFailed(_('Token is blacklisted.'))

        try:
            user = get_user_model().objects.get(
                **{api_settings.USER_ID_FIELD: payload['user_id']}
            )
        except get_user_model().DoesNotExist as error:
            raise AuthenticationFailed(_('User not found.')) from error

        if not api_settings.USER_AUTHENTICATION_RULE(user):
            raise AuthenticationFailed(_('User is inactive.'))

        outstanding, created = OutstandingToken.objects.get_or_create(
            jti=payload['jti'],
            defaults={
                'user': user,
                'token': raw_token,
                'expires_at': datetime_from_epoch(payload['exp']),
            },
        )
        BlacklistedToken.objects.get_or_create(token=outstanding)
        return Response(issue_token_pair(user))
