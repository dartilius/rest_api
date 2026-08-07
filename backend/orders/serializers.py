# orders/serializers.py

from datetime import time, datetime as dt

from rest_framework import serializers

from api.constants import Constants
from files.models import File, Playlist, TYPES
from nomenclatures.models import Nomenclature
from orders.models import AdOrder, BgOrder


def serialize_nomenclature(client):
    """Return a frontend-ready nomenclature name."""

    brand_name = client.brand.name if client.brand else client.name
    nomenclature_name = ' '.join(
        part for part in (f'"{brand_name}"') if part
    )

    address = client.formatted_address
    if address:
        nomenclature_name = f'{nomenclature_name} {address}'

    return nomenclature_name


class DateTimeTZRangeField(serializers.DictField):
    """
    Поле для обработки интервалов вещания.
    """

    from psycopg.types.range import TimestamptzRange

    child_class = serializers.DateTimeField
    range_type = TimestamptzRange

    default_error_messages = dict(serializers.DictField.default_error_messages)
    default_error_messages.update({
        'too_much_content': 'Недопустимо наличие лишних ключей: {extra}.',
        'bound_ordering': 'Конец вещания не может быть раньше начала или текущего момента.',
        'no_bound': 'Не указана дата {bound} вещания.'
    })

    def __init__(self, **kwargs):
        self.child_attrs = kwargs.pop('child_attrs', {})
        self.child = self.child_class(**self.child_attrs)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        extra_content = list(set(data) - {'lower', 'upper', 'bounds', 'empty'})
        if extra_content:
            self.fail('too_much_content', extra=', '.join(map(str, extra_content)))

        validated_dict = {}
        for key in ('lower', 'upper'):
            if key not in data:
                bound = 'начала' if key == 'lower' else 'окончания'
                self.fail('no_bound', bound=bound)
            validated_dict[key] = self.child.run_validation(data[key])

        lower, upper = validated_dict.get('lower'), validated_dict.get('upper')
        if lower > upper or (lower < upper < dt.now()) or (lower == upper < dt.now().date()):
            self.fail('bound_ordering')

        for key in ('bounds', 'empty'):
            if key in data:
                validated_dict[key] = data[key]
        return self.range_type(**validated_dict)

    def to_representation(self, value):
        """Преобразует значение для вывода."""
        lower = None
        upper = None

        if value and value.lower:
            lower = f'{value.lower:%Y-%m-%d %H:%M:%S}'
        if value and value.upper:
            upper = f'{value.upper:%Y-%m-%d %H:%M:%S}'

        return {
            'lower': self.child.to_representation(lower) if lower else None,
            'upper': self.child.to_representation(upper) if upper else None
        }


class AdOrderSerializer(serializers.ModelSerializer):
    """Сериализация одного рекламного заказа."""

    broadcast_interval = DateTimeTZRangeField()
    clients = serializers.ListField(write_only=True)

    class Meta:
        fields = (
            'id', 'name', 'description', 'owner', 'clients',
            'playlist', 'slides', 'broadcast_interval',
            'broadcast_type', 'parameters', 'status', 'created'
        )
        read_only_fields = ('id', 'owner', 'created')
        model = AdOrder

    def validate(self, data):
        """Валидация заказа."""
        def _translate_error(err):
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
                f'Количество {time_val} должно быть в пределах {e_list[-1]}'
            )

        def _time_string_to_tuple(time_string: str, brc_type: int) -> tuple:
            """Переводим строку времени в кортеж."""
            missing = {
                1: 'смещение по времени',
                2: 'смещение по времени',
                3: 'время начала и окончания',
                4: 'время окончания',
                5: 'время начала'
            }
            if not time_string:
                raise serializers.ValidationError(
                    f'Необходимо указать {missing.get(brc_type, "время")} для данного типа вещания'
                )
            try:
                return tuple(map(int, time_string.split(':')))
            except ValueError:
                raise serializers.ValidationError(
                    'Время должно быть в формате ЧЧ(:ММ:СС)'
                )

        def _validate_daily_times(start: tuple, end: tuple) -> dict:
            """Валидация интервала времени ежедневного вещания."""
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
                    f'Такого кол-ва выходов в час ({count}) нет в списке допустимых: {possible_counts}'
                )
            return {'times_in_hour': count}

        def _validate_weight(weight: int) -> dict:
            """Валидация приоритета файла."""
            if not 0 <= weight <= 100:
                raise serializers.ValidationError(
                    'Приоритет файла должен быть в пределах от 0 до 100'
                )
            return {'weight': weight}

        def _validate_timedelta(timedelta: tuple) -> dict:
            """Валидация промежутка времени."""
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
            """Валидация триггеров рекламы."""
            possible_events = ['click', 'door_open', 'blablabla']
            possible_active_ad_actions = ['skip', 'stop', 'wait_until_end']

            if not event:
                raise serializers.ValidationError('Необходимо указать триггер запуска')
            if not active_ad:
                raise serializers.ValidationError('Необходимо указать поведение текущей рекламы')

            if event not in possible_events:
                raise serializers.ValidationError(
                    f'Триггера нет в списке допустимых'
                )
            if active_ad not in possible_active_ad_actions:
                raise serializers.ValidationError(
                    f'Такое поведение для текущей рекламы не предусмотрено'
                )
            return {'event': event, 'active_ad': active_ad}

        def validate_slides(slides: dict, update: bool) -> None:
            """Валидация слайдов."""
            empty_values = Constants.empty_values
            if update:
                playlist_id = str(self.instance.playlist.id)
            else:
                playlist_id = self.initial_data[0].get('playlist')

            playlist_obj = Playlist.objects.get(id=playlist_id)
            playlist_file_ids = list(map(str, playlist_obj.files.values_list('id', flat=True)))
            slide_files = list(slides.keys())
            bad_files = []

            for file in slide_files:
                if file not in playlist_file_ids:
                    bad_files.append(File.objects.get(id=file).name)

            if bad_files not in empty_values:
                raise serializers.ValidationError(
                    f'В слайдах указаны ролики, которых нет среди файлов плейлиста: {bad_files}'
                )

        def validate_parameters(parameters: dict, brc_type: int) -> dict:
            """Валидация параметров в зависимости от типа вещания."""
            v_parameters = dict()

            times_in_hour = parameters.get('times_in_hour')
            weight_val = parameters.get('weight', 50)
            event_val = parameters.get('event')
            ad_action = parameters.get('active_ad')
            start_time = parameters.get('start_time')
            end_time = parameters.get('end_time')
            timedelta_val = parameters.get('timedelta')

            if not times_in_hour:
                raise serializers.ValidationError(
                    'Не указан обязательный параметр: кол-во выходов в час'
                )

            v_parameters.update(_validate_times_in_hour(int(times_in_hour)))
            v_parameters.update(_validate_weight(int(weight_val)))

            match brc_type:
                case 1 | 2:
                    if not timedelta_val:
                        raise serializers.ValidationError(
                            'Для типа вещания 1 или 2 необходимо указать timedelta'
                        )
                    timedelta_val = _time_string_to_tuple(timedelta_val, brc_type)
                    v_parameters.update(_validate_timedelta(timedelta_val))

                case 3 | 4 | 5:
                    if brc_type in (3, 5) and not start_time:
                        raise serializers.ValidationError(
                            f'Для типа вещания {brc_type} необходимо указать start_time'
                        )
                    if brc_type in (3, 4) and not end_time:
                        raise serializers.ValidationError(
                            f'Для типа вещания {brc_type} необходимо указать end_time'
                        )

                    start_tuple = _time_string_to_tuple(start_time, brc_type) if start_time else (0, 0, 1)
                    end_tuple = _time_string_to_tuple(end_time, brc_type) if end_time else (23, 59, 58)
                    v_parameters.update(_validate_daily_times(start_tuple, end_tuple))

                case 6:
                    if not event_val or not ad_action:
                        raise serializers.ValidationError(
                            'Для типа вещания 6 необходимо указать event и active_ad'
                        )
                    v_parameters.update(_validate_trigger(event_val, ad_action))

            return {'parameters': v_parameters}

        # Основная логика
        brc_type: int = data.get('broadcast_type')
        validated_data = dict()

        if 'parameters' in data or not self.instance:
            try:
                params: dict = data.pop('parameters')
                validated_data.update(validate_parameters(params, brc_type))
            except KeyError:
                raise serializers.ValidationError('Не переданы параметры заказа.')

        if 'slides' in self.initial_data:
            slides_json: dict = self.initial_data.get('slides')
            if not isinstance(slides_json, dict):
                raise serializers.ValidationError(
                    f'Слайды переданы неправильным форматом: {type(slides_json)}. Ожидался json-словарь.'
                )
            validate_slides(slides_json, bool(self.instance))

        validated_data.update({**data})
        return validated_data

    def create(self, validated_data):
        """Внесение клиентов из списка айди."""
        client_ids = validated_data.pop('clients')
        clients = Nomenclature.active.filter(id__in=client_ids)
        order_list = []
        for client in clients:
            order_list.append(AdOrder(client=client, **validated_data))
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

            # Преобразуем slides в читаемый вид
            repr_['slides'] = obj.slides if obj.slides else None

            # Преобразуем parameters в читаемый вид
            params = obj.parameters if obj.parameters else {}
            formatted_params = {}

            if 'times_in_hour' in params:
                formatted_params['times_in_hour'] = params['times_in_hour']
            if 'weight' in params:
                formatted_params['weight'] = params['weight']
            if 'timedelta' in params:
                timedelta_val = params['timedelta']
                if isinstance(timedelta_val, (list, tuple)):
                    formatted_params['timedelta'] = f"{timedelta_val[0]:02d}:{timedelta_val[1]:02d}:{timedelta_val[2]:02d}"
                else:
                    formatted_params['timedelta'] = timedelta_val
            if 'start_time' in params:
                start = params['start_time']
                if isinstance(start, (list, tuple)):
                    formatted_params['start_time'] = f"{start[0]:02d}:{start[1]:02d}:{start[2]:02d}"
                else:
                    formatted_params['start_time'] = start
            if 'end_time' in params:
                end = params['end_time']
                if isinstance(end, (list, tuple)):
                    formatted_params['end_time'] = f"{end[0]:02d}:{end[1]:02d}:{end[2]:02d}"
                else:
                    formatted_params['end_time'] = end
            if 'event' in params:
                formatted_params['event'] = params['event']
            if 'active_ad' in params:
                formatted_params['active_ad'] = params['active_ad']

            repr_['parameters'] = formatted_params
            repr_['created'] = f'{obj.created:%Y-%m-%d %H:%M:%S}'
            return repr_

        if isinstance(value, list):
            return [_serialize_order(item) for item in value]
        else:
            return _serialize_order(value)


class AdOrderListSerializer(serializers.ModelSerializer):
    """Сериализация списка рекламных заказов."""

    broadcast_interval = DateTimeTZRangeField()
    nomenclature = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id', 'name', 'owner', 'client', 'status',
            'broadcast_interval', 'broadcast_type', 'nomenclature'
        )
        read_only_fields = fields
        model = AdOrder

    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_['owner'] = value.owner.full_name if value.owner else None
        repr_['client'] = {
            'id': value.client.id,
            'name': value.client.name
        }
        return repr_

    def get_nomenclature(self, obj):
        return serialize_nomenclature(obj.client)


class BgOrderSerializer(serializers.ModelSerializer):
    """Сериализация одного фонового заказа."""

    broadcast_interval = DateTimeTZRangeField()
    clients = serializers.ListField(write_only=True)

    class Meta:
        fields = (
            'id', 'name', 'description', 'owner', 'clients',
            'order_type', 'playlist', 'broadcast_interval',
            'parameters', 'status', 'created',
            'is_permanent'
        )
        read_only_fields = ('id', 'owner', 'created')
        model = BgOrder

    def validate(self, data):
        """Валидация фонового заказа."""
        def _validate_playlist(playlist_id: str, order_type: int):
            empty_values = Constants.empty_values
            try:
                playlist_obj = Playlist.objects.get(id=playlist_id)
            except Playlist.DoesNotExist:
                raise serializers.ValidationError(f'Плейлист с id {playlist_id} не существует')

            files = playlist_obj.files.all()
            if files in empty_values:
                raise serializers.ValidationError('Плейлист не содержит файлов')

            for file in files:
                if file.type != order_type:
                    raise serializers.ValidationError(
                        f'Плейлист содержит файлы неправильного типа. '
                        f'Тип файла "{TYPES[file.type]}" ({file.type}) '
                        f'не соответствует типу заказа "{TYPES[order_type]}" ({order_type})'
                    )

        def _get_data_from_initial(key):
            if isinstance(self.initial_data, list):
                if len(self.initial_data) > 0:
                    return self.initial_data[0].get(key)
                else:
                    raise serializers.ValidationError('Получен пустой список данных')
            else:
                return self.initial_data.get(key)

        if self.instance:
            if 'playlist' in self.initial_data:
                playlist_id = _get_data_from_initial('playlist')
                order_type = self.instance.order_type
                _validate_playlist(playlist_id, order_type)
        else:
            playlist_id = _get_data_from_initial('playlist')
            order_type = _get_data_from_initial('order_type')

            if not playlist_id:
                raise serializers.ValidationError('Не указан плейлист')
            if order_type is None:
                raise serializers.ValidationError('Не указан тип заказа')

            _validate_playlist(playlist_id, order_type)
        return data

    def create(self, validated_data):
        """Внесение клиентов из списка айди."""
        client_ids = validated_data.pop('clients')
        clients = Nomenclature.active.filter(id__in=client_ids)

        if not clients.exists():
            raise serializers.ValidationError('Не найдено ни одной активной номенклатуры с указанными ID')

        order_list = []
        for client in clients:
            order_list.append(BgOrder(client=client, **validated_data))
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

            # Преобразуем parameters в читаемый вид
            params = obj.parameters if obj.parameters else {}
            formatted_params = {}

            if 'times_in_hour' in params:
                formatted_params['times_in_hour'] = params['times_in_hour']
            if 'weight' in params:
                formatted_params['weight'] = params['weight']
            if 'timedelta' in params:
                timedelta_val = params['timedelta']
                if isinstance(timedelta_val, (list, tuple)):
                    formatted_params['timedelta'] = f"{timedelta_val[0]:02d}:{timedelta_val[1]:02d}:{timedelta_val[2]:02d}"
                else:
                    formatted_params['timedelta'] = timedelta_val
            if 'start_time' in params:
                start = params['start_time']
                if isinstance(start, (list, tuple)):
                    formatted_params['start_time'] = f"{start[0]:02d}:{start[1]:02d}:{start[2]:02d}"
                else:
                    formatted_params['start_time'] = start
            if 'end_time' in params:
                end = params['end_time']
                if isinstance(end, (list, tuple)):
                    formatted_params['end_time'] = f"{end[0]:02d}:{end[1]:02d}:{end[2]:02d}"
                else:
                    formatted_params['end_time'] = end

            repr_['parameters'] = formatted_params
            repr_['created'] = f'{obj.created:%Y-%m-%d %H:%M:%S}'
            return repr_

        if isinstance(value, list):
            return [_serialize_order(item) for item in value]
        else:
            return _serialize_order(value)


class BgOrderListSerializer(serializers.ModelSerializer):
    """Сериализация списка фоновых заказов."""

    broadcast_interval = DateTimeTZRangeField()
    nomenclature = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id', 'name', 'owner', 'client', 'order_type', 'status',
            'broadcast_interval', 'is_permanent', 'nomenclature'
        )
        read_only_fields = fields
        model = BgOrder

    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_['owner'] = value.owner.full_name if value.owner else None
        repr_['client'] = {
            'id': value.client.id,
            'name': value.client.name
        }
        return repr_

    def get_nomenclature(self, obj):
        return serialize_nomenclature(obj.client)
