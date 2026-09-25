"""JWT issuance and the temporary HS256-to-RS256 migration boundary."""

from datetime import datetime, timezone

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.utils import datetime_from_epoch


def legacy_window_is_open():
    """Return whether old HS256 tokens are still allowed to be converted."""
    deadline = settings.JWT_LEGACY_HS256_ACCEPT_UNTIL
    secret = settings.JWT_LEGACY_HS256_SECRET
    if not deadline or not secret:
        return False

    try:
        parsed = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
    except ValueError:
        return False

    if parsed.tzinfo is None:
        return False
    return datetime.now(timezone.utc) < parsed.astimezone(timezone.utc)


def issue_token_pair(user):
    """Issue a fresh RS256 pair with server-side user state in its claims."""
    refresh = RefreshToken.for_user(user)
    refresh['role'] = user.role
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Add the current application role to every newly issued pair."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        return token


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """Rotate a refresh token and reload mutable user claims from the DB."""

    def validate(self, attrs):
        refresh = self.token_class(attrs['refresh'])
        user_id = refresh.payload.get(api_settings.USER_ID_CLAIM)
        if not user_id:
            raise AuthenticationFailed(
                self.error_messages['no_active_account'],
                'no_active_account',
            )

        try:
            user = get_user_model().objects.get(
                **{api_settings.USER_ID_FIELD: user_id}
            )
        except get_user_model().DoesNotExist as error:
            raise AuthenticationFailed(
                self.error_messages['no_active_account'],
                'no_active_account',
            ) from error

        if not api_settings.USER_AUTHENTICATION_RULE(user):
            raise AuthenticationFailed(
                self.error_messages['no_active_account'],
                'no_active_account',
            )

        if api_settings.BLACKLIST_AFTER_ROTATION:
            refresh.blacklist()

        return issue_token_pair(user)


class LegacyAccessToken(dict):
    """Minimal legacy token object that preserves logout blacklisting."""

    def __init__(self, payload, raw_token):
        super().__init__(payload)
        self.raw_token = raw_token

    def blacklist(self):
        jti = self.get(api_settings.JTI_CLAIM)
        exp = self.get('exp')
        if not jti or not exp:
            raise TokenError(_('Token has no blacklist identifier'))

        user = None
        user_id = self.get('user_id')
        if user_id:
            user = get_user_model().objects.filter(
                **{api_settings.USER_ID_FIELD: user_id}
            ).first()

        outstanding, _ = OutstandingToken.objects.get_or_create(
            jti=jti,
            defaults={
                'user': user,
                'token': self.raw_token,
                'expires_at': datetime_from_epoch(exp),
            },
        )
        return BlacklistedToken.objects.get_or_create(token=outstanding)


class DualJWTAuthentication(JWTAuthentication):
    """Verify RS256 first, then temporarily accept a valid old HS256 access."""

    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except InvalidToken as rs256_error:
            try:
                legacy_token = self.get_legacy_validated_token(raw_token)
                return self.get_legacy_user(legacy_token), legacy_token
            except AuthenticationFailed:
                raise rs256_error

    def get_legacy_validated_token(self, raw_token):
        if not legacy_window_is_open():
            raise AuthenticationFailed(_('Legacy JWT support has expired.'))

        try:
            payload = jwt.decode(
                raw_token,
                settings.JWT_LEGACY_HS256_SECRET,
                algorithms=['HS256'],
                options={'require': ['exp', 'jti', 'token_type', 'user_id']},
            )
        except jwt.PyJWTError as error:
            raise AuthenticationFailed(_('Invalid legacy JWT.')) from error

        if payload.get('token_type') != 'access':
            raise AuthenticationFailed(_('Wrong token type.'))
        if BlacklistedToken.objects.filter(token__jti=payload['jti']).exists():
            raise AuthenticationFailed(_('Token is blacklisted.'))
        return LegacyAccessToken(payload, raw_token.decode())

    def get_legacy_user(self, validated_token):
        try:
            user = self.user_model.objects.get(
                **{api_settings.USER_ID_FIELD: validated_token['user_id']}
            )
        except self.user_model.DoesNotExist as error:
            raise AuthenticationFailed(_('User not found.')) from error

        if not api_settings.USER_AUTHENTICATION_RULE(user):
            raise AuthenticationFailed(_('User is inactive.'))
        return user

