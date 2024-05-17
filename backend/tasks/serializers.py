from rest_framework import serializers

from tasks.models import Task

from nomenclatures.serializers import NomenclatureSerializer
from users.serializers import CustomUserSerializer


class TaskSerializer(serializers.ModelSerializer):
    """Сериализация репликаций."""

    owner = CustomUserSerializer(read_only=True)
    client = NomenclatureSerializer()

    class Meta:
        fields = (
            'id',
            'owner',
            'client',
            'type',
            'parameters',
            'created',
            'updated',
            'status'
        )
        read_only_fields = (
            'id',
            'owner',
            'client',  # ???
            'created',
            'updated',
            'status'
        )
        model = Task

