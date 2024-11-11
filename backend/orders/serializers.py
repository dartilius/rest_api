from datetime import time, datetime as dt
from rest_framework import serializers

from nomenclatures.models import Nomenclature
from orders.models import AdOrder, BgOrder


class DateTimeTZRangeField(serializers.DictField):
    """
    Поле для обработки интервалов вещания.

    1. Проверяем, что в полученных данных нет лишних ключей.
    2. Проверяем, что обязательные ключи (начало, конец) переданы.
    3. Проверяем, что начало не позже конца.
    4. Если всё ок - возвращаем как есть.
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
        extra_content = list(set(data) - {'lower', 'upper', 'bounds', 'empty'})
        # 1
        if extra_content:
            self.fail(
                'too_much_content', extra=', '.join(map(str, extra_content))
            )

        validated_dict = {}
        # 2
        for key in ('lower', 'upper'):
            if key not in data:
                bound = 'начала' if key == 'lower' else 'окончания'
                self.fail('no_bound', bound=bound)
            validated_dict[key] = self.child.run_validation(data[key])

        lower, upper = validated_dict.get('lower'), validated_dict.get('upper')
        # 3
        if lower > upper or upper < dt.now():
            self.fail('bound_ordering')

        for key in ('bounds', 'empty'):
            if key in data:
                validated_dict[key] = data[key]
        # 4
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

    broadcast_interval = DateTimeTZRangeField()
    clients = serializers.ListField(write_only=True)

    class Meta:
        fields = (
            'id',
            'name',
            'description',
            'owner',
            'clients',
            'playlist',
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

        def _time_string_to_tuple(time_string: str):
            try:
                return tuple(map(int, time_string.split(':')))
            except (ValueError, AttributeError):
                raise serializers.ValidationError(
                    'Временя должно быть в формате ЧЧ(:ММ:СС)'
                )

        def _validate_daily_times(start: str, end: str) -> dict:
            """Валидация интервала времени ежедневного вещания."""
            start = _time_string_to_tuple(start)
            end = _time_string_to_tuple(end)
            try:
                start_time = time(*start)
                end_time = time(*end)
            except ValueError as e:
                _translate_error(e)
            if not time(0, 0, 0) <= start_time < end_time <= time(23, 59, 59):
                raise serializers.ValidationError(
                    'Неправильно задан интервал времени ежедневного вещания'
                )
            validated_times = dict()
            if start != (0, 0, 1):
                validated_times.update({'start_time': start})
            if end != (23, 59, 58):
                validated_times.update({'end_time': end})
            return validated_times

        def _validate_times_in_hour(count: int) -> dict:
            """Валидация кол-ва выходов в час."""
            possible_counts = [1, 2, 3, 4, 6, 12]
            if count not in possible_counts:
                raise serializers.ValidationError(
                    f'Такого кол-ва выходов в час ({count}) '
                    f'нет в списке допустимых: {possible_counts}'
                )
            return {'times_in_hour': count}

        def _validate_weight(weight: int) -> dict:
            """Валидация приоритета файла."""
            if not 0 <= weight <= 100:
                raise serializers.ValidationError(
                    'Приоритет файла должен быть в пределах от 0 до 100'
                )
            return {'weight': weight}

        def _validate_timedelta(timedelta: str) -> dict:
            """Валидация промежутка времени."""
            timedelta = _time_string_to_tuple(timedelta)
            try:
                timedelta_time = time(*timedelta)
            except ValueError as e:
                _translate_error(e)
            if not time(0, 0, 59) < timedelta_time:
                raise serializers.ValidationError(
                    'Смещение по времени не может быть меньше 1 минуты'
                )
            return {'timedelta': timedelta}

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
            return {'event': event,
                    'active_ad': active_ad}

        try:
            brc_type: int = data.get('broadcast_type')
            parameters: dict = data.pop('parameters')
        except KeyError as e:
            raise serializers.ValidationError(
                f'Не указан обязательный параметр: {e}'
            )
        v_parameters = dict()

        try:
            # 1
            times_in_hour = parameters.get('times_in_hour')
            weight_val = parameters.get('weight') or 50
            event_val = parameters.get('event')
            ad_action = parameters.get('active_ad')
            start_time = parameters.get('daily_start_time')
            end_time = parameters.get('daily_end_time')
            timedelta_val = parameters.get('timedelta')
            # 2
            if times_in_hour is None:
                raise serializers.ValidationError(
                    f'Не указан обязательный параметр: кол-во выходов в час'
                )
            # 4
            v_parameters.update(_validate_times_in_hour(int(times_in_hour)))
            v_parameters.update(_validate_weight(int(weight_val)))
            # 3
            match brc_type:
                # 3.1
                case 1 | 2:
                    if timedelta_val is None:
                        raise serializers.ValidationError(
                            'Необходимо указать смещение по времени '
                            'для данного типа вещания'
                        )
                    # 4
                    v_parameters.update(_validate_timedelta(timedelta_val))
                # 3.2
                case 3:
                    if start_time is None or end_time is None:
                        raise serializers.ValidationError(
                            'Необходимо указать время начала и окончания '
                            'для данного типа вещания'
                        )
                    # 4
                    v_parameters.update(_validate_daily_times(start_time,
                                                              end_time))
                # 3.2
                case 4:
                    if end_time is None:
                        raise serializers.ValidationError(
                            'Необходимо указать время окончания '
                            'для данного типа вещания'
                        )
                    # 4
                    v_parameters.update(_validate_daily_times('00:00:01',
                                                              end_time))
                # 3.2
                case 5:
                    if start_time is None:
                        raise serializers.ValidationError(
                            'Необходимо указать время начала '
                            'для данного типа вещания'
                        )
                    # 4
                    v_parameters.update(_validate_daily_times(start_time,
                                                              '23:59:58'))
                # 3.3
                case 6:
                    if event_val is None or ad_action is None:
                        raise serializers.ValidationError(
                            'Необходимо указать триггер запуска и поведение '
                            'текущей рекламы для данного типа вещания'
                        )
                    # 4
                    v_parameters.update(_validate_trigger(event_val, ad_action))
        # 5
        except Exception as e:
            raise serializers.ValidationError(e)

        validated_data = {**data,
                          'parameters': v_parameters}
        return validated_data

    def create(self, validated_data):
        """Внесение клиентов из списка айди."""
        client_ids = validated_data.pop('clients')
        clients = Nomenclature.objects.filter(id__in=client_ids)
        order_list = []
        for client in clients:
            order_list.append(AdOrder(client=client,
                                      **validated_data))
        saved_orders = AdOrder.objects.bulk_create(order_list)
        return saved_orders

    def to_representation(self, value):
        """Десериализация с поддержкой списка объектов."""
        def _serialize_order(obj):
            repr_ = super(self.__class__, self).to_representation(obj)
            repr_['owner'] = obj.owner.full_name
            repr_['client'] = {
                'id': obj.client.id,
                'name': obj.client.name
            }
            repr_['playlist'] = {
                'id': obj.playlist.id,
                'name': obj.playlist.name,
                'files_count': obj.playlist.files.count()
            }
            repr_['slides'] = obj.slides if obj.slides else None
            repr_['created'] = obj.created.strftime('%Y-%m-%d %H:%M:%S')
            return repr_

        if isinstance(value, list):
            return [_serialize_order(order) for order in value]
        else:
            return _serialize_order(value)


class AdOrderListSerializer(serializers.ModelSerializer):
    """Сериализация списка рекламных заказов."""

    broadcast_interval = DateTimeTZRangeField()

    class Meta:
        fields = (
            'id',
            'name',
            'client',
            'playlist',
            'slides',
            'status',
            'broadcast_interval'
        )
        read_only_fields = fields
        model = AdOrder

    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_['client'] = {
            'id': value.client.id,
            'name': value.client.name
        }
        repr_['playlist'] = {
            'id': value.playlist.id,
            'name': value.playlist.name,
            'files_count': value.playlist.files.count()
        }
        return repr_


class BgOrderSerializer(serializers.ModelSerializer):
    """Сериализация одного фонового заказа."""

    broadcast_interval = DateTimeTZRangeField()
    clients = serializers.ListField(write_only=True)

    class Meta:
        fields = (
            'id',
            'name',
            'description',
            'owner',
            'clients',
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

    def validate(self, data):
        """
        Валидация фонового заказа.

        0. Получаем тип заказа и плейлист из пришедших данных.
        1. Находим плейлист в базе и проверяем:
        1.1. что плейлист не пуст,
        1.2. что тип файлов в плейлисте соответствует типу заказа.
        2. Если всё ок, возвращаем данные как есть.
        """
        from files.models import Playlist
        from api.constants import Constants

        empty_values = Constants.empty_values
        # 0
        order_type = data.get('order_type')
        playlist_id = self.initial_data[0].get('playlist')
        # 1
        playlist_obj = Playlist.objects.get(id=playlist_id)
        files = playlist_obj.files.all()
        # 1.1
        if files in empty_values:
            raise serializers.ValidationError('Плейлист не содержит файлов')
        # 1.2
        for file in files:
            if file.type != order_type:
                raise serializers.ValidationError(
                    f'Плейлист содержит файлы неправильного типа'
                )
        # 2
        return data

    def create(self, validated_data):
        """Внесение клиентов из списка айди."""
        client_ids = validated_data.pop('clients')
        clients = Nomenclature.objects.filter(id__in=client_ids)
        order_list = []
        for client in clients:
            order_list.append(BgOrder(client=client,
                                      **validated_data))
        saved_orders = BgOrder.objects.bulk_create(order_list)
        return saved_orders

    def to_representation(self, value):
        """Десериализация с поддержкой списка объектов."""
        def _serialize_order(obj):
            repr_ = super(self.__class__, self).to_representation(obj)
            repr_['owner'] = obj.owner.full_name
            repr_['client'] = {
                'id': obj.client.id,
                'name': obj.client.name
            }
            repr_['playlist'] = {
                'id': obj.playlist.id,
                'name': obj.playlist.name,
                'files_count': obj.playlist.files.count()
            }
            repr_['created'] = obj.created.strftime('%Y-%m-%d %H:%M:%S')
            return repr_

        if isinstance(value, list):
            return [_serialize_order(order) for order in value]
        else:
            return _serialize_order(value)


class BgOrderListSerializer(serializers.ModelSerializer):
    """Сериализация списка фоновых заказов."""

    broadcast_interval = DateTimeTZRangeField()

    class Meta:
        fields = (
            'id',
            'name',
            'client',
            'order_type',
            'playlist',
            'status',
            'broadcast_interval'
        )
        read_only_fields = fields
        model = BgOrder

    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_['client'] = {
            'id': value.client.id,
            'name': value.client.name
        }
        repr_['playlist'] = {
            'id': value.playlist.id,
            'name': value.playlist.name,
            'files_count': value.playlist.files.count()
        }
        return repr_
