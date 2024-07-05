import json
from datetime import time, timedelta as td
from rest_framework import serializers

from files.models import Playlist
from nomenclatures.models import NomenclatureGroup, Nomenclature
from orders.models import AdOrder, BgOrder, BROADCAST_TYPES


class DateTimeTZRangeField(serializers.DictField):
    """
    Поле для обработки интервалов вещания.

    Сделано на основе:
    https://github.com/Hipo/drf-extra-fields/
    """

    from psycopg.types.range import TimestamptzRange

    child_class = serializers.DateTimeField
    range_type = TimestamptzRange

    default_error_messages = dict(serializers.DictField.default_error_messages)
    default_error_messages.update({
        'too_much_content': 'Недопустимо наличие лишних ключей: {extra}.',
        'bound_ordering': 'Начало интервала не может быть позже окончания.',
        'no_bound': 'Не указана дата {bound} вещания.'
    })

    def __init__(self, **kwargs):
        self.child_attrs = kwargs.pop('child_attrs', {})
        self.child = self.child_class(**self.child_attrs)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        data = json.loads(data)

        extra_content = list(set(data) - {'lower', 'upper', 'bounds', 'empty'})
        if extra_content:
            self.fail(
                'too_much_content', extra=', '.join(map(str, extra_content))
            )

        validated_dict = {}
        for key in ('lower', 'upper'):
            if key not in data:
                bound = 'начала' if key == 'lower' else 'окончания'
                self.fail('no_bound', bound=bound)
            validated_dict[key] = self.child.run_validation(data[key])

        lower, upper = validated_dict.get('lower'), validated_dict.get('upper')
        if lower > upper:
            self.fail('bound_ordering')

        for key in ('bounds', 'empty'):
            if key in data:
                validated_dict[key] = data[key]

        return self.range_type(**validated_dict)

    def to_representation(self, value):
        # временный фикс отображения времени для UTC+7
        lower = (value.lower + td(hours=7)).strftime('%Y-%m-%d %H:%M:%S')
        upper = (value.upper + td(hours=7)).strftime('%Y-%m-%d %H:%M:%S')
        return {
            'since': self.child.to_representation(lower),
            'until': self.child.to_representation(upper)
        }


class AdOrderSerializer(serializers.ModelSerializer):
    """Сериализация одного рекламного заказа."""

    group = serializers.SlugRelatedField(
        slug_field='id',
        queryset=NomenclatureGroup.objects.all(),
        write_only=True
    )
    broadcast_interval = DateTimeTZRangeField()

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

    def validate_broadcast_type(self, data) -> None:
        """
        Валидация типа вещания.

        Для несуществующих типов вещания вызывается ошибка валидации,
        в остальных случаях тип вещания передаётся в фунцию валидации
        параметров заказа
        """
        broadcast_type: int = data.get('broadcast_type')

        if broadcast_type not in BROADCAST_TYPES:
            raise serializers.ValidationError('Тип вещания задан неверно')

        self.custom_validate_parameters(data.get('parameters'), broadcast_type)

    def custom_validate_parameters(self, value, brc_type: int) -> None:
        """
        Валидация параметров заказа.
        В зависимости от типа вещания валидируются соответствующие параметры.

        1. Пытаемся получить все возможные параметры. Если параметр не задан,
            то он будет None, кроме приоритета, который по-умолчанию 50.
        2. Обязательно должно быть указано кол-во выходов в час.
        3. Для типов вещания...
        3.1 ...со смещением по времени, оно должно быть задано.
        3.2 ...с любыми фиксированными часами вещания, они должны быть заданы.
        3.3 ...с триггером, должен быть задан запускающий триггер и вариант
            поведения для текущей рекламы.
        4. Каждая настройка отдельно валидируется в соответствующей функции.
        5. Любые исключения вызывают ошибку валидации с пояснением.
        """

        def _validate_daily_times(start: int, end: int) -> None:
            """Валидация интервала времени ежедневного вещания."""
            try:
                start = time(start)
                end = time(end)
            except ValueError as e:
                # Это всё нужно для перевода стандартной ошибки time
                time_val = str()
                e_list = str(e).split()
                match e_list[0]:
                    case 'second': time_val = 'секунд'
                    case 'minute': time_val = 'минут'
                    case 'hour': time_val = 'часов'
                raise serializers.ValidationError(
                    f'Количество {time_val} должно быть '
                    f'в пределах {e_list[-1]}'
                )
            if not time(0, 0, 0) <= start < end <= time(23, 59, 59):
                raise serializers.ValidationError(
                    'Неправильно задан интервал времени ежедневного вещания'
                )

        def _validate_times_in_hour(count: int) -> None:
            """Валидация кол-ва выходов в час."""
            possible_counts = [1, 2, 3, 4, 6, 12]
            if count not in possible_counts:
                raise serializers.ValidationError(
                    f'Количество выходов в час может быть только '
                    f'одним из {possible_counts}'
                )

        def _validate_weight(weight: int) -> None:
            """Валидация приоритета файла."""
            if not 0 <= weight <= 100:
                raise serializers.ValidationError(
                    'Приоритет файла должен быть в пределах от 0 до 100'
                )

        def _validate_timedelta(timedelta: int) -> None:
            """Валидация промежутка времени."""
            try:
                timedelta = time(timedelta)
            except ValueError as e:
                # Это всё нужно для перевода стандартной ошибки time
                time_val = str()
                e_list = str(e).split()
                match e_list[0]:
                    case 'second': time_val = 'секунд'
                    case 'minute': time_val = 'минут'
                    case 'hour': time_val = 'часов'
                raise serializers.ValidationError(
                    f'Количество {time_val} должно быть '
                    f'в пределах {e_list[-1]}'
                )
            if not time(0, 0, 0) <= timedelta:
                raise serializers.ValidationError(
                    'Смещение по времени не может быть меньше или равным 0'
                )

        def _validate_trigger(event: str, active_ad: str) -> None:
            """
            Валидация триггеров рекламы.

            possible_events : list
                список допустимых триггеров
            possible_active_ad_actions : list
                список допустимых действий, которые применяются
                к текущей рекламе, при срабатывании триггера
            """
            possible_events = ['click', 'door_open', 'blablabla']
            possible_active_ad_actions = ['skip', 'stop', 'wait_until_end']
            if event not in possible_events:
                raise serializers.ValidationError(
                    f'Триггера нет в списке доступных'
                )
            if active_ad not in possible_active_ad_actions:
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

            if times_in_hour is None:
                raise serializers.ValidationError(
                    f'Не указан обязательный параметр: кол-во выходов в час'
                )

            _validate_times_in_hour(times_in_hour)
            _validate_weight(weight_val)

            match brc_type:
                case 1 | 2:
                    if timedelta_val is None:
                        raise serializers.ValidationError(
                            'Необходимо указать смещение по времени '
                            'для данного типа вещания'
                        )
                    _validate_timedelta(*timedelta_val)
                case 3:
                    if start_time is None or end_time is None:
                        raise serializers.ValidationError(
                            'Необходимо указать время начала и окончания '
                            'для данного типа вещания'
                        )
                    _validate_daily_times(*start_time, *end_time)
                case 4:
                    if end_time is None:
                        raise serializers.ValidationError(
                            'Необходимо указать время окончания '
                            'для данного типа вещания'
                        )
                    _validate_daily_times(0, *end_time)
                case 5:
                    if timedelta_val is None:
                        raise serializers.ValidationError(
                            'Необходимо указать время начала '
                            'для данного типа вещания'
                        )
                    _validate_daily_times(*start_time, 0)
                case 6:
                    if event_val is None or ad_action is None:
                        raise serializers.ValidationError(
                            'Необходимо указать триггер запуска и поведение '
                            'текущей рекламы для данного типа вещания'
                        )
                    _validate_trigger(event_val, ad_action)

        except Exception as e:
            raise serializers.ValidationError(e)

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['owner'] = (
            f'{value.owner.last_name} {value.owner.first_name}'
        )
        representation['group'] = {'id': value.group.id,
                                   'name': value.group.name}
        representation['file'] = {'id': value.file.id, 'name': value.file.name}
        representation['slides'] = [
            {
                'id': slide.id,
                'name': slide.name
            } for slide in value.slides.all()
        ] if value.slides.exists() else None
        # временный фикс отображения времени для UTC+7
        representation['created'] = (
                value.created + td(hours=7)
        ).strftime('%Y-%m-%d %H:%M:%S')
        return representation


class AdOrderListSerializer(serializers.ModelSerializer):
    """Сериализация списка рекламных заказов."""

    broadcast_interval = DateTimeTZRangeField()

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
        representation['file'] = {'id': value.file.id, 'name': value.file.name}
        return representation


class BgOrderSerializer(serializers.ModelSerializer):
    """Сериализация одного фонового заказа."""

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
    broadcast_interval = DateTimeTZRangeField()

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
        representation['playlist'] = {
            'id': value.playlist.id,
            'name': value.playlist.name
        }
        # временный фикс отображения времени для UTC+7
        representation['created'] = (
                value.created + td(hours=7)
        ).strftime('%Y-%m-%d %H:%M:%S')
        return representation


class BgOrderListSerializer(serializers.ModelSerializer):
    """Сериализация списка фоновых заказов."""

    broadcast_interval = DateTimeTZRangeField()

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
        representation['playlist'] = {
            'id': value.playlist.id,
            'name': value.playlist.name
        }
        return representation
