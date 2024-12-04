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
        repr_ = super().to_representation(value)
        repr_['owner'] = value.owner.full_name
        repr_['client'] = {
            'id': str(value.client.id),
            'name': value.client.name
        }
        repr_['created'] = f'{value.created:%Y-%m-%d %H:%M:%S}'
        repr_['updated'] = f'{value.updated:%Y-%m-%d %H:%M:%S}'
        return repr_


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
        repr_ = super().to_representation(value)
        repr_['owner'] = value.owner.full_name
        repr_['client'] = {
            'id': str(value.client.id),
            'name': value.client.name
        }
        repr_['created'] = f'{value.created:%Y-%m-%d %H:%M:%S}'
        repr_['updated'] = f'{value.updated:%Y-%m-%d %H:%M:%S}'
        return repr_
