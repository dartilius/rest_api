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

        self.base_url = os.getenv("URL_1C")
        if not self.base_url:
            raise ValueError("Переменная окружения URL_1C не задана")

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

    def _save_token(self, xrmccookie: str) -> None:
        user = self._get_service_user()
        user.token_1c_access = xrmccookie
        user.save(update_fields=["token_1c_access"])

    def _auth_headers(self) -> dict:
        token = self._user.token_1c_access
        if not token:
            raise RuntimeError("Токен 1С не инициализирован. Выполните: python manage.py auth_1c")
        return {"xrmccookie": token}

    def _reauthenticate(self) -> bool:
        password = os.getenv("SERVICE_1C_PASSWORD")
        if not password:
            logger.error("SERVICE_1C_PASSWORD не задан")
            return False
        return self.authenticate(password)

    def authenticate(self, password: str) -> bool:
        user = self._get_service_user()
        url = f"{self.base_url}/ControlUser"
        payload = {"Почта": user.email, "Пароль": password}

        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error("Ошибка авторизации в 1С: %s", e)
            return False

        if not data.get("Результат"):
            logger.error("1С: ошибка авторизации — %s", data.get("Ответ"))
            return False

        if data.get("Блокировка"):
            logger.error("1С: пользователь заблокирован до %s", data["Блокировка"])
            return False

        xrmccookie = data.get("xrmccookie")
        if not xrmccookie:
            logger.error("1С не вернул xrmccookie. Ответ: %s", data)
            return False

        self._save_token(xrmccookie)
        return True

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        timeout = kwargs.pop("timeout", 30)
        headers.update(self._auth_headers())

        response = self.session.request(method, url, headers=headers, timeout=timeout, **kwargs)

        if response.status_code == 401:
            logger.warning("401 от 1С — переавторизация")
            if self._reauthenticate():
                headers.update(self._auth_headers())
                response = self.session.request(method, url, headers=headers, timeout=timeout, **kwargs)
            else:
                logger.error("Переавторизация не удалась")

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