import json
from datetime import time, datetime as dt
from rest_framework import serializers

from files.models import Playlist
from nomenclatures.models import NomenclatureGroup
from orders.models import AdOrder, BgOrder


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
        'bound_ordering': 'Конец вещания не может быть раньше начала или '
                          'текущего момента.',
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
        if lower > upper or upper < dt.now():
            self.fail('bound_ordering')

        for key in ('bounds', 'empty'):
            if key in data:
                validated_dict[key] = data[key]

        return self.range_type(**validated_dict)

    def to_representation(self, value):
        lower = value.lower.strftime('%Y-%m-%d %H:%M:%S')
        upper = value.upper.strftime('%Y-%m-%d %H:%M:%S')
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

    def validate(self, data):
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

        def _translate_error(err):
            """Это нужно для перевода стандартной ошибки time"""
            time_val = str()
            e_list = str(err).split()
            match e_list[0]:
                case 'second':
                    time_val = 'секунд'
                case 'minute':
                    time_val = 'минут'
                case 'hour':
                    time_val = 'часов'
            raise serializers.ValidationError(
                f'Количество {time_val} должно быть '
                f'в пределах {e_list[-1]}'
            )

        def _validate_daily_times(start: int, end: int) -> dict:
            """Валидация интервала времени ежедневного вещания."""
            try:
                start = time(start)
                end = time(end)
            except ValueError as e:
                _translate_error(e)
            if not time(0, 0, 0) <= start < end <= time(23, 59, 59):
                raise serializers.ValidationError(
                    'Неправильно задан интервал времени ежедневного вещания'
                )
            return {"start_time": start,
                    "end_time": end}

        def _validate_times_in_hour(count: int) -> dict:
            """Валидация кол-ва выходов в час."""
            possible_counts = [1, 2, 3, 4, 6, 12]
            if count not in possible_counts:
                raise serializers.ValidationError(
                    f'Такого кол-ва выходов в час ({count}) '
                    f'нет в списке допустимых: {possible_counts}'
                )
            return {"times_in_hour": count}

        def _validate_weight(weight: int) -> dict:
            """Валидация приоритета файла."""
            if not 0 <= weight <= 100:
                raise serializers.ValidationError(
                    'Приоритет файла должен быть в пределах от 0 до 100'
                )
            return {"weight": weight}

        def _validate_timedelta(timedelta: int) -> dict:
            """Валидация промежутка времени."""
            try:
                timedelta = time(timedelta)
            except ValueError as e:
                _translate_error(e)
            if not time(0, 0, 59) < timedelta:
                raise serializers.ValidationError(
                    'Смещение по времени не может быть меньше 1 минуты'
                )
            return {"timedelta": timedelta}

        def _validate_trigger(event: str, active_ad: str) -> dict:
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
                    f'Триггера нет в списке допустимых'
                )
            if active_ad not in possible_active_ad_actions:
                raise serializers.ValidationError(
                    f'Такое поведение для текущей рекламы не предусмотрено'
                )
            return {"event": event,
                    "active_ad": active_ad}

        brc_type: int = data.get('broadcast_type')
        parameters: dict = data.pop('parameters')
        v_parameters = dict()

        try:
            times_in_hour = parameters.get('times_in_hour')
            weight_val = parameters.get('weight') or 50
            event_val = parameters.get('event')
            ad_action = parameters.get('active_ad')
            start_time = parameters.get('daily_start_time')
            end_time = parameters.get('daily_end_time')
            timedelta_val = parameters.get('timedelta')

            if times_in_hour is None:
                raise serializers.ValidationError(
                    f'Не указан обязательный параметр: кол-во выходов в час'
                )

            v_parameters.update(_validate_times_in_hour(int(times_in_hour)))
            v_parameters.update(_validate_weight(int(weight_val)))

            match brc_type:
                case 1 | 2:
                    if timedelta_val is None:
                        raise serializers.ValidationError(
                            'Необходимо указать смещение по времени '
                            'для данного типа вещания'
                        )
                    _timedelta = tuple(map(int, timedelta_val.split(':')))
                    v_parameters.update(_validate_timedelta(*_timedelta))
                case 3:
                    if start_time is None or end_time is None:
                        raise serializers.ValidationError(
                            'Необходимо указать время начала и окончания '
                            'для данного типа вещания'
                        )
                    start = tuple(map(int, start_time.split(':')))
                    end = tuple(map(int, end_time.split(':')))
                    v_parameters.update(_validate_daily_times(*start, *end))
                case 4:
                    if end_time is None:
                        raise serializers.ValidationError(
                            'Необходимо указать время окончания '
                            'для данного типа вещания'
                        )
                    end = tuple(map(int, end_time.split(':')))
                    v_parameters.update(_validate_daily_times(0, *end))
                case 5:
                    if start_time is None:
                        raise serializers.ValidationError(
                            'Необходимо указать время начала '
                            'для данного типа вещания'
                        )
                    start = tuple(map(int, start_time.split(':')))
                    v_parameters.update(_validate_daily_times(*start, 0))
                case 6:
                    if event_val is None or ad_action is None:
                        raise serializers.ValidationError(
                            'Необходимо указать триггер запуска и поведение '
                            'текущей рекламы для данного типа вещания'
                        )
                    v_parameters.update(_validate_trigger(event_val, ad_action))

        except Exception as e:
            raise serializers.ValidationError(e)

        validated_data = {**data, "parameters": v_parameters}
        return validated_data

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['owner'] = (
            f'{value.owner.last_name} {value.owner.first_name}'
        )
        representation['group'] = {'id': value.group.id,
                                   'name': value.group.name}
        representation['file'] = {'id': value.file.id, 'name': value.file.name}
        representation['slides'] = [
            {'id': slide.id,
             'name': slide.name} for slide in value.slides.all()
        ] if value.slides.exists() else None
        representation['created'] = value.created.strftime('%Y-%m-%d %H:%M:%S')
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
        representation['slides'] = [
            {'id': slide.id,
             'name': slide.name} for slide in value.slides.all()
        ] if value.slides.exists() else None
        representation['file'] = {'id': value.file.id, 'name': value.file.name}
        return representation


class BgOrderSerializer(serializers.ModelSerializer):
    """Сериализация одного фонового заказа."""

    group = serializers.SlugRelatedField(
        slug_field='id',
        queryset=NomenclatureGroup.objects.all(),
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
            'group',
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
        representation['group'] = {'id': value.group.id,
                                   'name': value.group.name}
        representation['playlist'] = {
            'id': value.playlist.id,
            'name': value.playlist.name
        }
        representation['created'] = value.created.strftime('%Y-%m-%d %H:%M:%S')
        return representation


class BgOrderListSerializer(serializers.ModelSerializer):
    """Сериализация списка фоновых заказов."""

    broadcast_interval = DateTimeTZRangeField()

    class Meta:
        fields = (
            'id',
            'name',
            'group',
            'order_type',
            'playlist',
            'status',
            'broadcast_interval'
        )
        read_only_fields = fields
        model = BgOrder

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['group'] = {'id': value.group.id,
                                   'name': value.group.name}
        representation['playlist'] = {
            'id': value.playlist.id,
            'name': value.playlist.name
        }
        return representation
