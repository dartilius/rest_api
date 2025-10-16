import os
import requests
from typing import Optional


class APIService:
    """
    Глобальный сервис для взаимодействия с внешним API (1C или аналог).
    Реализует авторизацию и методы работы с брендами.
    """

    def __init__(self):
        self.base_url = os.getenv("URL_1C")
        if not self.base_url:
            raise ValueError("⚠️ Переменная окружения URL_1C не задана")

        self.session = requests.Session()
        self.xrmccookie: Optional[str] = None

    # ---------- Авторизация ----------
    def authenticate(self, username: str, password: str) -> bool:
        """
        Авторизация на внешнем API. Возвращает True, если удалось.
        Оставляет в self.xrmccookie токен для последующих запросов.
        """
        url = f"{self.base_url}/ControlUser"
        data = {"Почта": username, "Пароль": password}

        try:
            response = self.session.post(url, json=data, timeout=10)
            response.raise_for_status()
            data = response.json()

            # В ответе нам нужен только xrmccookie
            self.xrmccookie = data.get("xrmccookie")
            return bool(self.xrmccookie)
        except requests.RequestException as e:
            with open('/app/network_logs/err.log', 'a', encoding='utf-8') as f:
                f.write(f"{username}:{password}\n")
                f.write(f"❌ Ошибка авторизации: {e}\n")
            return False

    # ---------- Создание бренда ----------
    def create_brand(self, brand_name: str, brand_description: Optional[str] = None) -> dict:
        """
        POST /CreateBrand
        """
        if not self.xrmccookie:
            raise RuntimeError("Нет токена авторизации. Сначала вызови authenticate().")

        url = f"{self.base_url}/CreateBrand"
        payload = {
            "brandName": brand_name,
            "brandDescription": brand_description or "",
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "xrmccookie": self.xrmccookie,
        }

        response = self.session.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        with open('/app/network_logs/test.log', 'a', encoding='utf-8') as f:
            f.write(f'{brand_name}: {response.json()}\n')
        return response.json()

    # ---------- Обновление бренда ----------
    def update_brand(self, brand_code: str, brand_name: str, brand_description: str) -> dict:
        """
        PATCH /UpdateBrand
        """
        if not self.xrmccookie:
            raise RuntimeError("Нет токена авторизации. Сначала вызови authenticate().")

        url = f"{self.base_url}/UpdateBrand"
        payload = {
            "brandCode": brand_code,
            "brandName": brand_name,
            "brandDescription": brand_description,
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "xrmccookie": self.xrmccookie,
        }

        response = self.session.patch(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

    # ---------- Добавление логотипа ----------
    def add_logo_to_brand(self, brand_code: str, logotype: str) -> dict:
        """
        POST /AddLogoToBrand
        """
        if not self.xrmccookie:
            raise RuntimeError("Нет токена авторизации. Сначала вызови authenticate().")

        url = f"{self.base_url}/AddLogoToBrand"
        payload = {
            "brandCode": brand_code,
            "brandLogoBase64": logotype,
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "xrmccookie": self.xrmccookie,
        }

        response = self.session.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
