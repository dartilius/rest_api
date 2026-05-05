import os
import logging
import requests
from datetime import timedelta
from typing import TYPE_CHECKING
from django.utils import timezone
from typing import cast
from django.contrib.auth import get_user_model
if TYPE_CHECKING:
    from users.models import CustomUser

logger = logging.getLogger(__name__)

def get_service_user() -> CustomUser:
    email = os.getenv("SERVICE_1C_EMAIL")
    if not email:
        raise ValueError("Переменная окружения SERVICE_1C_EMAIL не задана")
    return cast(CustomUser, get_user_model().objects.get(email=email))

class APIService:
    """
    Сервис для взаимодействия с 1С.
    Привязан к конкретному superuser-у — токены хранятся на его инстансе.
    """

    EXPIRY_BUFFER = timedelta(minutes=5)

    def __init__(self, user: 'CustomUser'):
        self.base_url = os.getenv("URL_1C")
        if not self.base_url:
            raise ValueError("Переменная окружения URL_1C не задана")

        if not user.is_super_user:
            raise PermissionError(f"Пользователь {user.full_name} не является superuser-ом 1С")

        self.user = user
        self.session = requests.Session()

    # ---------- Внутренние ----------

    def _save_tokens(
        self,
        access: str,
        refresh: str,
        access_expires_at,
        refresh_expires_at=None,
    ) -> None:
        self.user.token_1c_access = access
        self.user.token_1c_refresh = refresh
        self.user.token_1c_access_expires_at = access_expires_at
        self.user.token_1c_refresh_expires_at = refresh_expires_at
        self.user.save(update_fields=[
            "token_1c_access",
            "token_1c_refresh",
            "token_1c_access_expires_at",
            "token_1c_refresh_expires_at",
        ])

    def _ensure_valid_access(self) -> str:
        """
        Возвращает валидный access-токен.
        Рефрешит превентивно за EXPIRY_BUFFER до истечения.
        """
        if not self.user.token_1c_access:
            raise RuntimeError(f"Токены для {self.user.email} не инициализированы.")

        expires_at = self.user.token_1c_access_expires_at
        if expires_at and timezone.now() >= expires_at - self.EXPIRY_BUFFER:
            logger.info("Access-токен %s истекает, выполняем refresh", self.user.email)
            if not self.refresh_tokens():
                raise RuntimeError(f"Не удалось обновить токен для {self.user.email}.")
            # После refresh перечитываем из БД
            self.user.refresh_from_db()

        return self.user.token_1c_access

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self._ensure_valid_access()}"}

    def _handle_token_response(self, data: dict, keep_refresh: str = None) -> bool:
        """Разбирает ответ 1С и сохраняет токены."""
        access = data.get("access")
        refresh = data.get("refresh") or keep_refresh

        if not access or not refresh:
            logger.error("1С не вернул токены. Ответ: %s", data)
            return False

        now = timezone.now()

        access_expires_in = data.get("access_expires_in")
        access_expires_at = (
            now + timedelta(seconds=int(access_expires_in))
            if access_expires_in
            else now + timedelta(hours=1)
        )
        if not access_expires_in:
            logger.warning("1С не вернул access_expires_in, fallback: 1h")

        refresh_expires_in = data.get("refresh_expires_in")
        refresh_expires_at = (
            now + timedelta(seconds=int(refresh_expires_in))
            if refresh_expires_in
            else None
        )

        self._save_tokens(access, refresh, access_expires_at, refresh_expires_at)
        return True

    # ---------- Авторизация ----------

    def authenticate(self, password: str) -> bool:
        """
        Первичная авторизация пользователя в 1С.
        Username берём из self.user.email.
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

        return self._handle_token_response(data)

    def refresh_tokens(self) -> bool:
        """Обновляет access через refresh-токен пользователя."""
        if not self.user.token_1c_refresh:
            logger.error("Refresh-токен отсутствует у %s", self.user.email)
            return False

        if self.user.token_1c_refresh_is_expired:
            logger.error("Refresh-токен истёк у %s. Нужна повторная авторизация.", self.user.email)
            return False

        url = f"{self.base_url}/RefreshToken"
        payload = {"refresh": self.user.token_1c_refresh}

        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error("Ошибка refresh для %s: %s", self.user.email, e)
            return False

        return self._handle_token_response(data, keep_refresh=self.user.token_1c_refresh)

    # ---------- Базовый запрос ----------

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        headers.update(self._auth_headers())
        return self.session.request(method, url, headers=headers, timeout=10, **kwargs)

    # ---------- Методы API ----------

    def send_feedback(self, feedback: 'Feedback') -> bool:
        """
        Отправляет обращение из модели Feedback в 1С.
        Возвращает True при успехе.
        """
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