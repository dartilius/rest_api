import re
from urllib.parse import urlsplit

from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from feedback.models import Feedback
from feedback.request_data import BroadcastRequestDataSerializer, StrictBooleanField
from placement_order.serializers import AttributionField

# Bump this when the actual consent wording on the site changes.
CONSENT_VERSION = "corporate-broadcast-v1"


class FeedbackSerializer(serializers.ModelSerializer):
    brandId = serializers.CharField(source="brand_id", required=False, allow_null=True, allow_blank=True)
    nomenclaturesIds = serializers.ListField(child=serializers.CharField(), source="nomenclatures_ids", required=False, allow_null=True)
    attribution = AttributionField(required=False, allow_null=True)
    request_data = BroadcastRequestDataSerializer(required=False)
    consent = StrictBooleanField(required=False)

    class Meta:
        model = Feedback
        fields = ["id", "code1c", "name", "phone", "email", "message", "pathname",
                  "brandId", "nomenclaturesIds", "attribution", "created",
                  "request_type", "company", "request_data", "consent", "consent_at", "consent_version"]
        read_only_fields = ["id", "created", "consent_at", "consent_version"]

    def validate(self, attrs):
        request_type = attrs.get("request_type", Feedback.RequestType.GENERAL)
        if request_type != Feedback.RequestType.CORPORATE_BROADCAST:
            if attrs.get("request_data"):
                raise serializers.ValidationError({"request_data": "Параметры доступны для корпоративного вещания."})
            return attrs
        errors = {}
        # Prevent silently dropping typos and client-supplied consent metadata.
        for key in self.initial_data.keys() - self.fields.keys():
            errors[key] = "Неизвестное поле."
        for key in ("id", "created", "consent_at", "consent_version"):
            if key in self.initial_data:
                errors[key] = "Поле заполняется сервером."
        for key, limit in {"name": 150, "phone": 40, "email": 254, "message": 5000, "pathname": 500}.items():
            value = (attrs.get(key) or "").strip()
            attrs[key] = value
            if len(value) > limit:
                errors[key] = f"Не более {limit} символов."
        if len(attrs["name"]) < 2:
            errors["name"] = "Укажите имя: минимум 2 символа."
        pathname = attrs["pathname"]
        if pathname:
            try:
                parsed = urlsplit(pathname)
            except ValueError:
                parsed = None
            if (parsed is None or not pathname.startswith("/") or pathname.startswith("//")
                    or parsed.scheme or parsed.netloc or parsed.query or parsed.fragment
                    or "\\" in pathname or any(ord(char) < 32 for char in pathname)):
                errors["pathname"] = "Передайте только путь страницы без query-строки и фрагмента."
        phone, email = attrs["phone"], attrs["email"]
        if not phone and not email:
            errors["phone"] = "Укажите телефон или email."
            errors["email"] = "Укажите телефон или email."
        if phone and (not re.fullmatch(r"[+\d ()-]+", phone) or not 10 <= len(re.sub(r"\D", "", phone)) <= 15):
            errors["phone"] = "Укажите корректный телефон (10–15 цифр)."
        if email:
            try:
                validate_email(email)
            except DjangoValidationError:
                errors["email"] = "Укажите корректный email."
        if attrs.get("consent") is not True:
            errors["consent"] = "Необходимо согласие на обработку персональных данных."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def create(self, validated_data):
        if validated_data.get("consent") is True:
            validated_data["consent_at"] = timezone.now()
            validated_data["consent_version"] = (
                CONSENT_VERSION
                if validated_data.get("request_type") == Feedback.RequestType.CORPORATE_BROADCAST
                else "feedback-v1"
            )
        return super().create(validated_data)
