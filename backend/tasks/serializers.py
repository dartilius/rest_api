from rest_framework import serializers

from nomenclatures.models import Nomenclature
from tasks.models import Task


class TaskSerializer(serializers.ModelSerializer):
    """Сериализация одной репликации."""

    client = serializers.SlugRelatedField(
        slug_field='id',
        queryset=Nomenclature.objects.all(),
        write_only=True
    )

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
            'created',
            'updated'
        )
        model = Task

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['owner'] = {
            'full_name': f'{value.owner.last_name} {value.owner.first_name}'
        }
        representation['client'] = {
            'id': value.client.id,
            'name': value.client.name
        }
        representation['created'] = value.created.strftime('%Y-%m-%d %H:%M:%S')
        representation['updated'] = value.updated.strftime('%Y-%m-%d %H:%M:%S')
        return representation


class TaskListSerializer(serializers.ModelSerializer):
    """Сериализация списка репликаций."""

    class Meta:
        fields = (
            'id',
            'owner',
            'client',
            'type',
            'created',
            'updated',
            'status'
        )
        read_only_fields = fields
        model = Task

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['owner'] = {
            'full_name': f'{value.owner.last_name} {value.owner.first_name}'
        }
        representation['client'] = {
            'id': value.client.id,
            'name': value.client.name
        }
        representation['created'] = value.created.strftime('%Y-%m-%d %H:%M:%S')
        representation['updated'] = value.updated.strftime('%Y-%m-%d %H:%M:%S')
        return representation


class WorkstationSerializer(serializers.Serializer):
    """Сериализация общения с рабочей станцией."""

    version = serializers.CharField(max_length=100, required=True)
    tasks = serializers.ListField(required=True)
    hw_info = serializers.HStoreField(required=True)
