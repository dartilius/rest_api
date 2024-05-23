from rest_framework_simplejwt.tokens import AccessToken, BlacklistMixin


class CustomAccessToken(BlacklistMixin, AccessToken):
    """Токен авторизации."""
