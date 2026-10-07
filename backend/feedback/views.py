from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, OpenApiResponse
from rest_framework import mixins, serializers, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle

from feedback.models import Feedback
from feedback.serializers import FeedbackSerializer

class FeedbackErrorSerializer(serializers.Serializer):
    detail = serializers.CharField(required=False)


@extend_schema_view(create=extend_schema(
    tags=['Обратная связь'],
    description="Публичная общая ручка. Без request_type создаёт прежнее общее обращение. Для corporate_broadcast обязательны имя, телефон или email и consent=true. request_data необязателен. 201 означает сохранение заявки; доставка письма выполняется отдельно.",
    responses={201: FeedbackSerializer, 400: OpenApiResponse(description="Ошибки по полям; ошибки конструктора вложены в request_data."), 429: FeedbackErrorSerializer},
    examples=[
        OpenApiExample("Общее обращение", value={"name": "Посетитель", "message": "Вопрос об услуге"}, request_only=True),
        OpenApiExample("Корпоративное вещание", value={"request_type": "corporate_broadcast", "name": "Посетитель", "phone": "+7 000 000-00-00", "company": "Пример компании", "pathname": "/corporate-broadcast", "consent": True, "request_data": {"object_count": 5, "format": "audio", "content": {"music": True, "announcements": True}}}, request_only=True),
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
