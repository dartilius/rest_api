import logging
import os
from typing import TYPE_CHECKING, cast

import requests
from django.contrib.auth import get_user_model

if TYPE_CHECKING:
    from users.models import CustomUser

logger = logging.getLogger(__name__)


class APIClient1C:
    """
    Singleton-клиент для взаимодействия с 1С.
    Используй: api_1c.get('/endpoint') / api_1c.post('/endpoint', payload)
    """

    _instance: 'APIClient1C | None' = None

    def __new__(cls) -> 'APIClient1C':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        base_url = os.getenv("URL_1C")
        if not base_url:
            raise ValueError("Переменная окружения URL_1C не задана")
        self.base_url = base_url.rstrip("/")

        self.session = requests.Session()
        self._initialized = True

    @staticmethod
    def _get_service_user() -> 'CustomUser':
        email = os.getenv("SERVICE_1C_EMAIL")
        if not email:
            raise ValueError("Переменная окружения SERVICE_1C_EMAIL не задана")
        return cast('CustomUser', get_user_model().objects.get(email=email))

    @property
    def _user(self) -> 'CustomUser':
        return self._get_service_user()

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _save_tokens(self, access: str, refresh: str | None = None) -> None:
        user = self._get_service_user()
        user.token_1c_access = access
        fields = ["token_1c_access"]
        if refresh is not None:
            user.token_1c_refresh = refresh
            fields.append("token_1c_refresh")
        user.save(update_fields=fields)

    def _auth_headers(self) -> dict:
        token = self._user.token_1c_access
        if not token:
            raise RuntimeError("Токен 1С не инициализирован. Выполните: python manage.py auth_1c")
        return {"Authorization": f"access_token {token}"}

    def _token_request(self, path: str, payload: dict) -> dict | None:
        try:
            response = self.session.post(self._url(path), json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as e:
            logger.error("Ошибка JWT-запроса в 1С (%s): %s", path, type(e).__name__)
            return None
        if not isinstance(data, dict):
            logger.error("1С вернул некорректный формат JWT-ответа (%s)", path)
            return None
        return data

    @staticmethod
    def _valid_token(token) -> bool:
        return isinstance(token, str) and bool(token.strip())

    def authenticate(self, password: str) -> bool:
        if not password:
            logger.error("Пароль сервисного пользователя 1С не задан")
            return False
        user = self._get_service_user()
        data = self._token_request(
            "/auth/jwt/create", {"email": user.email, "password": password}
        )
        if data is None:
            return False
        access, refresh = data.get("access"), data.get("refresh")
        if not self._valid_token(access) or not self._valid_token(refresh):
            logger.error("1С не вернул access/refresh при авторизации")
            return False
        self._save_tokens(access, refresh)
        return True

    def refresh_access(self) -> bool:
        refresh = self._user.token_1c_refresh
        if not refresh:
            logger.error("Refresh-токен 1С не инициализирован. Выполните auth_1c")
            return False
        data = self._token_request("/auth/jwt/refresh", {"refresh": refresh})
        if data is None:
            return False
        access = data.get("access")
        new_refresh = data.get("refresh")
        if not self._valid_token(access) or (
            "refresh" in data and not self._valid_token(new_refresh)
        ):
            logger.error("1С вернул некорректные токены при обновлении access")
            return False
        self._save_tokens(access, new_refresh)
        return True

    def ping(self) -> requests.Response:
        """Проверка доступности 1С без авторизации."""
        return self.session.get(self._url("/ping/open"), timeout=10)

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = self._url(path)
        headers = requests.structures.CaseInsensitiveDict(kwargs.pop("headers", {}) or {})
        timeout = kwargs.pop("timeout", 30)
        headers.update(self._auth_headers())

        response = self.session.request(method, url, headers=headers, timeout=timeout, **kwargs)

        if response.status_code == 403:
            logger.warning("403 от 1С — обновление access-токена")
            if self.refresh_access():
                headers.update(self._auth_headers())
                response = self.session.request(method, url, headers=headers, timeout=timeout, **kwargs)
            else:
                logger.error("Обновление access-токена 1С не удалось")

        return response

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        return self._request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, data: dict, **kwargs) -> requests.Response:
        return self._request("POST", endpoint, json=data, **kwargs)

    def patch(self, endpoint: str, data: dict, **kwargs) -> requests.Response:
        return self._request("PATCH", endpoint, json=data, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        return self._request("DELETE", endpoint, **kwargs)


api_1c = APIClient1C()
