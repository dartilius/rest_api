# import os
# import logging
# import requests
# from typing import TYPE_CHECKING, cast
# from django.contrib.auth import get_user_model
#
# if TYPE_CHECKING:
#     from users.models import CustomUser
#     from feedback.models import Feedback
#
# logger = logging.getLogger(__name__)
#
#
# def get_service_user() -> 'CustomUser':
#     email = os.getenv("SERVICE_1C_EMAIL")
#     if not email:
#         raise ValueError("Переменная окружения SERVICE_1C_EMAIL не задана")
#     return cast('CustomUser', get_user_model().objects.get(email=email))
#
#
# class APIService:
#     """
#     Сервис для взаимодействия с 1С.
#     Токены хранятся на инстансе CustomUser.
#     Срок жизни токенов контролирует 1С — при 401 выполняем refresh и повторяем запрос.
#     """
#
#     def __init__(self, user: 'CustomUser'):
#         self.base_url = os.getenv("URL_1C")
#         if not self.base_url:
#             raise ValueError("Переменная окружения URL_1C не задана")
#
#         if not user.is_super_user:
#             raise PermissionError(f"Пользователь {user.full_name} не является superuser-ом 1С")
#
#         self.user = user
#         self.session = requests.Session()
#
#     # ---------- Внутренние ----------
#
#     def _save_tokens(self, access: str, refresh: str) -> None:
#         self.user.token_1c_access = access
#         self.user.token_1c_refresh = refresh
#         self.user.save(update_fields=["token_1c_access", "token_1c_refresh"])
#
#     def _auth_headers(self) -> dict:
#         if not self.user.token_1c_access:
#             raise RuntimeError(f"Токены для {self.user.email} не инициализированы.")
#         return {"Authorization": f"Bearer {self.user.token_1c_access}"}
#
#     def _handle_token_response(self, data: dict, keep_refresh: str = None) -> bool:
#         access = data.get("access")
#         refresh = data.get("refresh") or keep_refresh
#
#         if not access or not refresh:
#             logger.error("1С не вернул токены. Ответ: %s", data)
#             return False
#
#         self._save_tokens(access, refresh)
#         return True
#
#     # ---------- Авторизация ----------
#
#     def authenticate(self, password: str) -> bool:
#         url = f"{self.base_url}/ControlUser"
#         payload = {"Почта": self.user.email, "Пароль": password}
#
#         try:
#             response = self.session.post(url, json=payload, timeout=10)
#             response.raise_for_status()
#             data = response.json()
#         except requests.RequestException as e:
#             logger.error("Ошибка авторизации %s в 1С: %s", self.user.email, e)
#             return False
#
#         return self._handle_token_response(data)
#
#     def refresh_tokens(self) -> bool:
#         if not self.user.token_1c_refresh:
#             logger.error("Refresh-токен отсутствует у %s", self.user.email)
#             return False
#
#         url = f"{self.base_url}/RefreshToken"
#         payload = {"refresh": self.user.token_1c_refresh}
#
#         try:
#             response = self.session.post(url, json=payload, timeout=10)
#             response.raise_for_status()
#             data = response.json()
#         except requests.RequestException as e:
#             logger.error("Ошибка refresh для %s: %s", self.user.email, e)
#             return False
#
#         return self._handle_token_response(data, keep_refresh=self.user.token_1c_refresh)
#
#     # ---------- Базовый запрос ----------
#
#     def _request(self, method: str, path: str, **kwargs) -> requests.Response:
#         """
#         Выполняет запрос. При 401 — рефрешит токен и повторяет один раз.
#         """
#         url = f"{self.base_url}{path}"
#         headers = kwargs.pop("headers", {})
#         headers.update(self._auth_headers())
#
#         response = self.session.request(method, url, headers=headers, timeout=10, **kwargs)
#
#         if response.status_code == 401:
#             logger.warning("401 от 1С для %s — пробуем refresh", self.user.email)
#             if self.refresh_tokens():
#                 self.user.refresh_from_db()
#                 headers.update(self._auth_headers())
#                 response = self.session.request(method, url, headers=headers, timeout=10, **kwargs)
#             else:
#                 logger.error("Refresh не удался для %s", self.user.email)
#
#         return response
#
#     # ---------- Методы API ----------
#
#     def send_feedback(self, feedback: 'Feedback') -> bool:
#         payload = {
#             "code1c": feedback.code1c,
#             "name": feedback.name,
#             "phone": feedback.phone,
#             "email": feedback.email,
#             "message": feedback.message,
#         }
#
#         try:
#             response = self._request("POST", "/Feedback", json=payload)
#             response.raise_for_status()
#             return True
#         except requests.RequestException as e:
#             logger.error("Ошибка отправки Feedback %s в 1С: %s", feedback.id, e)
#             return False

import logging
import os
from typing import TYPE_CHECKING, cast

import requests
from django.contrib.auth import get_user_model

from brands.models import Brand

if TYPE_CHECKING:
    from users.models import CustomUser
    from feedback.models import Feedback

logger = logging.getLogger(__name__)


def get_service_user() -> 'CustomUser':
    email = os.getenv("SERVICE_1C_EMAIL")
    if not email:
        raise ValueError("Переменная окружения SERVICE_1C_EMAIL не задана")
    return cast('CustomUser', get_user_model().objects.get(email=email))


class APIService:
    """
    Сервис для взаимодействия с 1С.
    Авторизация через /ControlUser — возвращает xrmccookie.
    При 401 — повторная авторизация через SERVICE_1C_PASSWORD.
    """

    def __init__(self, user: 'CustomUser'):
        self.base_url = os.getenv("URL_1C")
        if not self.base_url:
            raise ValueError("Переменная окружения URL_1C не задана")

        if not user.is_super_user:
            raise PermissionError(f"Пользователь {user.full_name} не является superuser-ом 1С")

        self.user = user
        self.session = requests.Session()

    # ---------- Внутренние ----------

    def _save_token(self, xrmccookie: str) -> None:
        self.user.token_1c_access = xrmccookie
        self.user.save(update_fields=["token_1c_access"])

    def _auth_headers(self) -> dict:
        if not self.user.token_1c_access:
            raise RuntimeError(f"Токен для {self.user.email} не инициализирован.")
        return {"xrmccookie": self.user.token_1c_access}

    # ---------- Авторизация ----------

    def authenticate(self, password: str) -> bool:
        """
        Авторизация в 1С. Сохраняет xrmccookie в БД.
        Ответ: Результат=false — ошибка, Блокировка != '' — заблокирован.
        """
        url = f"{self.base_url}/ControlUser"
        payload = {"Почта": self.user.email, "Пароль": password}

        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error("Ошибка авторизации %s в 1С: %s", self.user.email, e)
            return False

        if not data.get("Результат"):
            logger.error("1С: ошибка авторизации %s — %s", self.user.email, data.get("Ответ"))
            return False

        if data.get("Блокировка"):
            logger.error("1С: пользователь %s заблокирован до %s", self.user.email, data["Блокировка"])
            return False

        xrmccookie = data.get("xrmccookie")
        if not xrmccookie:
            logger.error("1С не вернул xrmccookie. Ответ: %s", data)
            return False

        self._save_token(xrmccookie)
        return True

    def _reauthenticate(self) -> bool:
        """Повторная авторизация при 401 через env-переменную."""
        password = os.getenv("SERVICE_1C_PASSWORD")
        if not password:
            logger.error("SERVICE_1C_PASSWORD не задан — невозможно переавторизоваться")
            return False
        return self.authenticate(password)

    # ---------- Базовый запрос ----------

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """При 401 — переавторизуется и повторяет запрос один раз."""
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        timeout = kwargs.pop("timeout", 30)
        headers.update(self._auth_headers())

        response = self.session.request(method, url, headers=headers, timeout=timeout, **kwargs)

        if response.status_code == 401:
            logger.warning("401 от 1С для %s — переавторизация", self.user.email)
            if self._reauthenticate():
                self.user.refresh_from_db()
                headers.update(self._auth_headers())
                response = self.session.request(method, url, headers=headers, timeout=timeout, **kwargs)
            else:
                logger.error("Переавторизация не удалась для %s", self.user.email)

        return response

    # ---------- Методы API ----------

    def send_feedback(self, feedback: 'Feedback') -> bool:
        payload = {
            "Код1С": feedback.code1c,
            "Имя": feedback.name,
            "Телефон": feedback.phone,
            "Почта": feedback.email,
            "Текст": feedback.message,
        }

        try:
            response = self._request("POST", "/Feedback", json=payload)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error("Ошибка отправки Feedback %s в 1С: %s", feedback.id, e)
            return False

    def create_brand(self, brand: 'Brand') -> str | None:
        """
        Создаёт бренд в 1С. Возвращает code1c (brandCode) или None при ошибке.
        """
        payload = {
            "brandName": brand.name,
            "brandDescription": brand.description or '',
        }

        try:
            response = self._request("POST", "/CreateBrand", json=payload)
            response.raise_for_status()
            data = response.json()

            brand_code = data.get("brandCode")
            if not brand_code:
                logger.warning("1С не вернул brandCode для бренда %s", brand.id)
                return None

            return brand_code
        except requests.RequestException as e:
            logger.error("Ошибка создания бренда %s в 1С: %s", brand.id, e)
            return None

