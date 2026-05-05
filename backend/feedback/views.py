from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from feedback.models import Feedback
from feedback.serializers import FeedbackSerializer
from services.api_1c_client import logger, api_1c
from rest_framework.status import (
    HTTP_201_CREATED
)
from rest_framework.response import Response

@extend_schema(tags=['Обратная связь'])
class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        feedback = serializer.save()

        try:
            response = api_1c.post("/feedback", {
                "code1c": feedback.name,
                "name": feedback.name,
                "phone": feedback.phone,
                "email": feedback.email,
                "message": feedback.message,
            })
            response.raise_for_status()
            return response.json().get("brandCode")
        except Exception as e:
            logger.warning("Не удалось создать бренд в 1С: %s", e)

        feedback_res = FeedbackSerializer(feedback)
        return Response(feedback_res.data, status=HTTP_201_CREATED)