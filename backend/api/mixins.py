from services.api_1c_client import APIService, get_service_user


class APIServiceMixin:
    """Миксин для вьюх, которым нужен доступ к 1С."""

    @property
    def svc(self) -> APIService:
        if not hasattr(self, '_svc'):
            self._svc = APIService(user=get_service_user())
        return self._svc