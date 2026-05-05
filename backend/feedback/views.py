from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from api import APIServiceMixin
from feedback.models import Feedback
from feedback.serializers import FeedbackSerializer
from services.api_1c_client import logger


@extend_schema(tags=['Обратная связь'])
class FeedbackViewSet(APIServiceMixin, viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        feedback = serializer.save()

        try:
            code1c = self.svc.send_feedback(feedback)
            if code1c:
                if Feedback.objects.filter(code1c=code1c).exclude(id=feedback.id).exists():
                    logger.warning("code1c %s уже занят другим обращением", code1c)
                else:
                    feedback.code1c = code1c
                    feedback.save(update_fields=["code1c"])
        except Exception as e:
            logger.warning("Не удалось отправить обращение в 1С: %s", e)