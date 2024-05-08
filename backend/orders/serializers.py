from rest_framework import serializers
from datetime import time

from api.logger import setup_logger

from orders.models import AdOrder, BgOrder

from nomenclatures.serializers import NomenclatureGroupSerializer
from files.serializers import PlaylistSerializer
from users.serializers import UserSerializer

logger = setup_logger('orders', '..orders.log')


class AdOrderSerializer(serializers.ModelSerializer):
    """Сериализация рекламных заказов."""

    owner = serializers.SerializerMethodField()
    group = NomenclatureGroupSerializer()
    playlist = PlaylistSerializer()

    class Meta:
        fields = (
            'id',
            'group',
            'owner',
            'name',
            'description',
            'broadcast_interval',
            'broadcast_type',
            'parameters',
            'file',
            'slides',
            'created'
        )
        read_only_fields = (
            'id',
            'owner',
            'created'
        )
        model = AdOrder

    def get_owner(self, obj):
        return f'{obj.owner.last_name} {obj.owner.first_name}'

    @staticmethod
    def default_parameters():
        return {
            "event": "play if click button",
            "active_ad": "close",
            "times_in_hour": 4,
            "weight": 50,
            "daily_start_time": "09:00:00",
            "daily_end_time": "21:00:00",
            "timedelta": "01:30:00"
        }

    BROADCAST_TYPES = {
        0: 'По времени работы точки',
        1: 'Начало работы + смещение по времени',
        2: 'Конец работы - смещение по времени',
        3: 'Конкретные часы',
        4: 'С открытия до фиксированного часа',
        5: 'С фиксированного часа до закрытия',
        6: 'Старт по событию'
    }

    def validate_broadcast_type(self, data):
        """Валидация типа вещания."""
        broadcast_type: int = data.get('broadcast_type')

        match broadcast_type:
            case 0 | 1 | 2 | 3 | 4 | 5 | 6: self.validate_parameters(
                data.get('parameters'), broadcast_type
            )
            case _:
                raise serializers.ValidationError(
                    'Тип вещания задан неверно'
                )

    def validate_parameters(self, value, brc_type: int) -> None:
        """Валидация параметров заказа."""

        def __validate_daily_times(start: int, end: int) -> None:
            try:
                start = time(start)
                end = time(end)
            except Exception as e:
                logger.exception(f'Возникла ошибка: {e}')
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
                logger.exception(f'Возникла ошибка: {e}')
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
            weight_val: int = value.get('weight')
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
                    if event_val is None or ad_action:
                        raise serializers.ValidationError(
                            'Необходимо указать триггер запуска и поведение '
                            'текущей рекламы для данного типа вещания'
                        )
                    __validate_trigger(event_val, ad_action)

        except Exception as e:
            logger.exception(f'Возникла ошибка: {e}')
            raise serializers.ValidationError(e)


class BgOrderSerializer(serializers.ModelSerializer):
    """Сериализация фоновых заказов."""

    owner = serializers.SerializerMethodField()
    group = NomenclatureGroupSerializer()
    playlist = PlaylistSerializer()

    class Meta:
        fields = (
            'id',
            'group',
            'owner',
            'name',
            'description',
            'broadcast_interval',
            'parameters',
            'playlist',
            'slides',
            'created'
        )
        read_only_fields = (
            'id',
            'owner',
            'created'
        )
        model = BgOrder

    def get_owner(self, obj):
        return f'{obj.owner.last_name} {obj.owner.first_name}'

    def validate_parameters(self, value):
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

        __validate_daily_times(
            *(map(int, value['daily_start_time'].split(':'))),
            *(map(int, value['daily_end_time'].split(':')))
        )
