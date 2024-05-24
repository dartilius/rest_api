from rest_framework import serializers
from datetime import time, timedelta as td

from files.models import Playlist
from nomenclatures.models import NomenclatureGroup, Nomenclature
from orders.models import AdOrder, BgOrder, BROADCAST_TYPES


class AdOrderSerializer(serializers.ModelSerializer):
    """Сериализация рекламных заказов."""

    group = serializers.SlugRelatedField(
        slug_field='id',
        queryset=NomenclatureGroup.objects.all(),
        write_only=True
    )

    class Meta:
        fields = (
            'id',
            'name',
            'description',
            'owner',
            'group',
            'file',
            'slides',
            'broadcast_interval',
            'broadcast_type',
            'parameters',
            'status',
            'created'
        )
        read_only_fields = (
            'id',
            'owner',
            'created'
        )
        model = AdOrder

    def validate_broadcast_type(self, data):
        """Валидация типа вещания."""
        broadcast_type: int = data.get('broadcast_type')

        if broadcast_type not in BROADCAST_TYPES:
            raise serializers.ValidationError('Тип вещания задан неверно')

        self.custom_validate_parameters(data.get('parameters'), broadcast_type)

    def custom_validate_parameters(self, value, brc_type: int) -> None:
        """Валидация параметров заказа."""

        def __validate_daily_times(start: int, end: int) -> None:
            try:
                start = time(start)
                end = time(end)
            except Exception as e:
                raise serializers.ValidationError(e)
            if not time(0, 0, 0) <= start < end <= time(23, 59, 59):
                raise serializers.ValidationError(
                    'Неправильно задан интервал времени ежедневного вещания'
                )

        def __validate_times_in_hour(count: int) -> None:
            possible_counts = [1, 2, 3, 4, 6, 12]
            if count not in possible_counts:
                raise serializers.ValidationError(
                    f'Количество выходов в час может быть только '
                    f'одним из {possible_counts}'
                )

        def __validate_weight(weight: int) -> None:
            if not 0 <= weight <= 100:
                raise serializers.ValidationError(
                    'Вес файла должен быть в пределах от 0 до 100'
                )

        def __validate_timedelta(timedelta: int) -> None:
            try:
                timedelta = time(timedelta)
            except Exception as e:
                raise serializers.ValidationError(e)
            if not time(0, 0, 0) <= timedelta:
                raise serializers.ValidationError(
                    'Смещение по времени не может быть нулевым'
                )

        def __validate_trigger(event: str, active_ad: str) -> None:
            possible_events = ['click', 'door_open', 'blablabla']
            possible_active_ad = ['skip', 'stop', 'wait_until_end']
            if event not in possible_events:
                raise serializers.ValidationError(
                    f'Триггера нет в списке доступных'
                )
            if active_ad not in possible_active_ad:
                raise serializers.ValidationError(
                    f'Такое поведение для текущей рекламы не предусмотрено'
                )

        try:
            times_in_hour: int = value.get('times_in_hour')
            weight_val: int = value.get('weight') or 50
            event_val: str = value.get('event')
            ad_action: str = value.get('active_ad')
            start_time = (map(int, value.get('daily_start_time').split(':')))
            end_time = (map(int, value.get('daily_end_time').split(':')))
            timedelta_val = (map(int, value.get('timedelta').split(':')))

            if times_in_hour is None or weight_val is None:
                raise serializers.ValidationError(
                    f'Не указан обязательный параметр '
                    f'кол-во выходов в час либо вес файла'
                )

            __validate_times_in_hour(times_in_hour)
            __validate_weight(weight_val)

            match brc_type:
                case 1 | 2:
                    if timedelta_val is None:
                        raise serializers.ValidationError(
                            'Необходимо указать смещение по времени '
                            'для данного типа вещания'
                        )
                    __validate_timedelta(*timedelta_val)
                case 3:
                    if start_time is None or end_time is None:
                        raise serializers.ValidationError(
                            'Необходимо указать время начала и окончания '
                            'для данного типа вещания'
                        )
                    __validate_daily_times(*start_time, *end_time)
                case 4:
                    if end_time is None:
                        raise serializers.ValidationError(
                            'Необходимо указать время окончания '
                            'для данного типа вещания'
                        )
                    __validate_daily_times(0, *end_time)
                case 5:
                    if timedelta_val is None:
                        raise serializers.ValidationError(
                            'Необходимо указать время начала '
                            'для данного типа вещания'
                        )
                    __validate_daily_times(*start_time, 0)
                case 6:
                    if event_val is None or ad_action is None:
                        raise serializers.ValidationError(
                            'Необходимо указать триггер запуска и поведение '
                            'текущей рекламы для данного типа вещания'
                        )
                    __validate_trigger(event_val, ad_action)

        except Exception as e:
            raise serializers.ValidationError(e)

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['owner'] = (
            f'{value.owner.last_name} {value.owner.first_name}'
        )
        representation['group'] = {'id': value.group.id, 'name': value.group.name}
        # в базе по местному, но на странице по UTC почему-то
        representation['broadcast_interval'] = {
            'from': (value.broadcast_interval.lower + td(hours=7)).strftime(
                '%Y-%m-%d %H:%M:%S'),
            'to': (value.broadcast_interval.upper + td(hours=7)).strftime(
                '%Y-%m-%d %H:%M:%S')
        }
        representation['file'] = {'id': value.file.id, 'name': value.file.name}
        representation['slides'] = [
            {
                'id': slide.id,
                'name': slide.name
            } for slide in value.slides.all()
        ] if value.slides.exists() else None
        representation['created'] = value.created.strftime('%Y-%m-%d %H:%M:%S')
        return representation


class AdOrderListSerializer(serializers.ModelSerializer):
    """Сериализация списка рекламных заказов."""

    class Meta:
        fields = (
            'id',
            'name',
            'group',
            'file',
            'slides',
            'status',
            'broadcast_interval'
        )
        read_only_fields = fields
        model = AdOrder

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['group'] = {
            'id': value.group.id,
            'name': value.group.name
        }
        representation['broadcast_interval'] = {
            'from': value.broadcast_interval.lower.strftime('%Y-%m-%d'),
            'to': value.broadcast_interval.upper.strftime('%Y-%m-%d')
        }
        representation['file'] = {'id': value.file.id, 'name': value.file.name}
        return representation


class BgOrderSerializer(serializers.ModelSerializer):
    """Сериализация фоновых заказов."""

    client = serializers.SlugRelatedField(
        slug_field='id',
        queryset=Nomenclature.objects.all(),
        write_only=True
    )
    playlist = serializers.SlugRelatedField(
        slug_field='id',
        queryset=Playlist.objects.all(),
        write_only=True
    )

    class Meta:
        fields = (
            'id',
            'name',
            'description',
            'owner',
            'client',
            'order_type',
            'playlist',
            'broadcast_interval',
            'status',
            'created'
        )
        read_only_fields = (
            'id',
            'owner',
            'created'
        )
        model = BgOrder

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['owner'] = {
            'full_name': f'{value.owner.last_name} {value.owner.first_name}'
        }
        representation['client'] = {
            'id': value.client.id,
            'name': value.client.name
        }
        # в базе по местному, но на странице по UTC почему-то
        representation['broadcast_interval'] = {
            'from': (value.broadcast_interval.lower + td(hours=7)).strftime(
                '%Y-%m-%d %H:%M:%S'),
            'to': (value.broadcast_interval.upper + td(hours=7)).strftime(
                '%Y-%m-%d %H:%M:%S')
        }
        representation['playlist'] = {
            'id': value.playlist.id,
            'name': value.playlist.name
        }
        representation['created'] = value.created.strftime('%Y-%m-%d %H:%M:%S')
        return representation


class BgOrderListSerializer(serializers.ModelSerializer):
    """Сериализация списка фоновых заказов."""

    class Meta:
        fields = (
            'id',
            'name',
            'client',
            'playlist',
            'status',
            'broadcast_interval'
        )
        read_only_fields = fields
        model = BgOrder

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['client'] = {
            'id': value.client.id,
            'name': value.client.name
        }
        representation['broadcast_interval'] = {
            'from': value.broadcast_interval.lower.strftime('%Y-%m-%d'),
            'to': value.broadcast_interval.upper.strftime('%Y-%m-%d')
        }
        representation['playlist'] = {
            'id': value.playlist.id,
            'name': value.playlist.name
        }
        return representation
