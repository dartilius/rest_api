from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from feedback.models import Feedback
from feedback.serializers import FeedbackSerializer
from services.api_1c_client import APIService, logger, get_service_user


@extend_schema(tags=['Обратная связь'])
class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        feedback = serializer.save()

        try:
            svc = APIService(user=get_service_user())
            svc.send_feedback(feedback)
        except Exception as e:
            logger.warning("Не удалось отправить Feedback в 1С: %s", e)