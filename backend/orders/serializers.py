from rest_framework import serializers

from orders.models import Order

from nomenclatures.serializers import NomenclatureGroupSerializer
from files.serializers import PlaylistSerializer
from users.serializers import UserSerializer


class OrderSerializer(serializers.ModelSerializer):
    """Сериализация заказов."""

    owner = UserSerializer(read_only=True)
    group = NomenclatureGroupSerializer()
    playlist = PlaylistSerializer()

    class Meta:
        fields = (
            'id',
            'owner',
            'name',
            'description',
            'group',
            'type',
            'broadcast_interval',
            'playlist',
            'created'
        )
        read_only_fields = (
            'id',
            'owner',
            'created'
        )
        model = Order
