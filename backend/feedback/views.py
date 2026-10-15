from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, OpenApiResponse
from rest_framework import mixins, serializers, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle

from feedback.models import Feedback
from feedback.serializers import FeedbackSerializer
from users.privacy import validate_consent
from rest_framework.exceptions import APIException

class FeedbackErrorSerializer(serializers.Serializer):
    detail = serializers.CharField(required=False)


@extend_schema_view(create=extend_schema(
    tags=['Обратная связь'],
    description="Для любого обращения обязательны boolean consent=true, consent_version=2026-10-14 и согласованный personal_data_consent с purpose=feedback. Время и источник фиксирует Django. 201 означает атомарное сохранение обращения и согласия; уведомление выполняется отдельно.",
    responses={201: FeedbackSerializer, 400: OpenApiResponse(description="Ошибки по полям; ошибки конструктора вложены в request_data."), 429: FeedbackErrorSerializer},
    examples=[
        OpenApiExample("Общее обращение", value={
            "name": "Посетитель", "message": "Вопрос об услуге", "consent": True,
            "consent_version": "2026-10-14", "personal_data_consent": {
                "accepted": True, "purpose": "feedback", "version": "2026-10-14",
            },
        }, request_only=True),
    ],
))
class FeedbackViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "feedback"

    def perform_create(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        validate_consent(request.data, 'feedback')
        try:
            return super().create(request, *args, **kwargs)
        except APIException:
            raise
        except Exception:
            raise APIException('Не удалось сохранить обращение. Попробуйте позже.') from None
