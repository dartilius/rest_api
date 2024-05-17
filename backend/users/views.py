from rest_framework import viewsets

from users.models import CustomUser
from users.permissions import IsSuperUserOrAuthReadOnly
from users.serializers import CustomUserSerializer, CustomUserListSerializer


class CustomUserViewSet(viewsets.ModelViewSet):
    """Работа с пользователями."""

    queryset = CustomUser.objects.all().order_by('id')
    serializer_class = CustomUserSerializer
    # permission_classes = [IsSuperUserOrAuthReadOnly, ]

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            serializer = CustomUserListSerializer
        else:
            serializer = CustomUserSerializer
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return serializer(*args, **kwargs)
