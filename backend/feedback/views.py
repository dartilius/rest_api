from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

from feedback.models import Feedback
from feedback.serializers import FeedbackSerializer

@extend_schema(tags=['Обратная связь'])
class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
