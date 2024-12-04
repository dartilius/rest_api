from datetime import time, datetime as dt
from rest_framework import serializers

from api.constants import Constants
from files.models import File, Playlist
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
        if (
            lower > upper or
            (lower < upper < dt.now()) or
            (lower == upper < dt.now().date())
        ):
            self.fail('bound_ordering')

        for key in ('bounds', 'empty'):
            if key in data:
                validated_dict[key] = data[key]
        # 4
        return self.range_type(**validated_dict)

    def to_representation(self, value):
        lower = f'{value.lower:%Y-%m-%d %H:%M:%S}'
        upper = f'{value.upper:%Y-%m-%d %H:%M:%S}'
        return {
            'lower': self.child.to_representation(lower),
            'upper': self.child.to_representation(upper)
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
        Валидация заказа.

        1. Запрашиваем тип заказа и JSON со слайдами из пришедших данных.
        2. Если были указанны параметры или идёт создание заказа, то тянем
            параметры из пришедших данных и валидируем. Причём параметры мы
            изымаем (.pop()) из данных, чтобы отбор прошли только необходимые
            для указанного типа заказа.
        3. Валидируем слайды, если они были указаны.
        4. Если данные проходят валидацию, возвращаем их.
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

        def _time_string_to_tuple(time_string: str, brc_type: int) -> tuple:
            """Переводим строку времени в кортеж."""
            missing = {1: 'смещение по времени',
                       2: 'смещение по времени',
                       3: 'время начала и окончания',
                       4: 'время окончания',
                       5: 'время начала'}
            try:
                return tuple(map(int, time_string.split(':')))
            except ValueError:
                raise serializers.ValidationError(
                    'Временя должно быть в формате ЧЧ(:ММ:СС)'
                )
            except AttributeError:
                raise serializers.ValidationError(
                    f'Необходимо указать {missing[brc_type]} '
                    'для данного типа вещания'
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
            """
            Валидация триггеров рекламы.

            possible_events : list
                список допустимых триггеров
            possible_active_ad_actions : list
                список допустимых действий, которые применяются
                к текущей рекламе, при срабатывании триггера

            1. Проверяем, все ли ключи переданы.
            2. Если чего-то не хватает, возвращаем ошибку, с указанием
                чего не хватает.
            3. Проверяем есть ли триггер/поведение в списке допустимых.
            4. Возвращаем словарь если всё ОК.
            """
            possible_events = ['click', 'door_open', 'blablabla']
            possible_active_ad_actions = ['skip', 'stop', 'wait_until_end']
            test = 0
            keys = {event: 1, active_ad: 2}
            missing = {1: 'триггер запуска',
                       2: 'поведение текущей рекламы',
                       3: 'триггер запуска и поведение текущей рекламы'}
            # 1
            for key in keys:
                test += keys[key] if not key else 0
            if test:
                # 2
                raise serializers.ValidationError(
                    f'Необходимо указать {missing[test]} для '
                    'данного типа вещания.'
                )
            # 3
            if event not in possible_events:
                raise serializers.ValidationError(
                    f'Триггера нет в списке допустимых'
                )
            # 3
            if active_ad not in possible_active_ad_actions:
                raise serializers.ValidationError(
                    f'Такое поведение для текущей рекламы не предусмотрено'
                )
            # 4
            return {'event': event,
                    'active_ad': active_ad}

        def validate_slides(slides: dict, update: bool) -> None:
            """
            Валидация слайдов.

            1. Запрашиваем айди плейлиста:
            1.1 Если происходит обновление существующего заказа,
                то тянем айди из поля объекта.
            1.1 Если происходит создание заказа, то из отправленных данных.
            2. Получаем объект плейлиста и список айди его файлов.
            3. Собираем список из указанных в слайдах роликов.
            4. Сравниваем списки. Если есть лишние ролики выбрасываем ошибку
                с указанием названий этих лишних роликов.
            """
            empty_values = Constants.empty_values
            # 1.1
            if update:
                playlist_id = str(self.instance.playlist.id)
            # 1.2
            else:
                playlist_id = self.initial_data[0].get('playlist')
            # 2
            playlist_obj = Playlist.objects.get(id=playlist_id)
            playlist_file_ids = playlist_obj.files.values_list('id', flat=True)
            playlist_file_ids = list(map(str, playlist_file_ids))
            # 3
            slide_files = [*slides.keys()]
            bad_files = []
            # 4
            for file in slide_files:
                if file not in playlist_file_ids:
                    bad_files.append(File.objects.get(id=file).name)
            if bad_files not in empty_values:
                raise serializers.ValidationError(
                    'В слайдах указаны ролики, которых нет '
                    f'среди файлов плейлиста: {bad_files}'
                )

        def validate_parameters(parameters: dict, brc_type: int) -> dict:
            """
            В зависимости от типа вещания валидируются соответствующие параметры.

            1. Все неуказанные параметры будут None, кроме приоритета,
                который по-умолчанию 50.
            2. Обязательно должно быть указано кол-во выходов в час.
            3. Для типов вещания...
            3.1 ...со смещением по времени, оно должно быть задано.
            3.2 ...с любыми фиксированными часами вещания, они должны быть заданы.
            3.3 ...с триггером, должен быть задан запускающий триггер и вариант
                поведения для текущей рекламы.
            4. Каждая настройка отдельно валидируется в соответствующей функции.
            5. Если в заказе указаны слайды, проверяем, что указанные среди слайдов
                файлы действительно есть в плейлисте заказа.
            """
            v_parameters = dict()
            # 1
            times_in_hour = parameters.get('times_in_hour')
            weight_val = parameters.get('weight', 50)
            event_val = parameters.get('event')
            ad_action = parameters.get('active_ad')
            start_time = parameters.get('daily_start_time')
            end_time = parameters.get('daily_end_time')
            timedelta_val = parameters.get('timedelta')
            # 2
            if not times_in_hour:
                raise serializers.ValidationError(
                    f'Не указан обязательный параметр: '
                    f'кол-во выходов в час'
                )
            # 4
            v_parameters.update(
                _validate_times_in_hour(int(times_in_hour))
            )
            v_parameters.update(_validate_weight(int(weight_val)))
            # 3
            match brc_type:
                # 3.1
                case 1 | 2:
                    timedelta_val = _time_string_to_tuple(timedelta_val, brc_type)
                    # 4
                    v_parameters.update(_validate_timedelta(timedelta_val))
                # 3.2
                case 3 | 4 | 5:
                    start_time = _time_string_to_tuple(start_time, brc_type) if (
                            brc_type in (3, 5)
                    ) else (0, 0, 1)
                    end_time = _time_string_to_tuple(end_time, brc_type) if (
                            brc_type in (3, 4)
                    ) else (23, 59, 58)
                    # 4
                    v_parameters.update(_validate_daily_times(start_time,
                                                              end_time))
                # 3.3
                case 6:
                    # 4
                    v_parameters.update(_validate_trigger(event_val,
                                                          ad_action))
            return {'parameters': v_parameters}

        # 1
        brc_type: int = data.get('broadcast_type')
        validated_data = dict()
        # 2
        if 'parameters' in data or not self.instance:
            try:
                params: dict = data.pop('parameters')
                validated_data.update(validate_parameters(params, brc_type))
            except KeyError:
                raise serializers.ValidationError(
                    'Не переданы параметры заказа.'
                )
        # 3
        if 'slides' in self.initial_data:
            slides_json: dict = self.initial_data.get('slides')
            if not isinstance(slides_json, dict):
                raise serializers.ValidationError(
                    'Слайды переданы неправильным форматом: '
                    f'{type(slides_json)}. Ожидался json-словарь.'
                )
            validate_slides(slides_json, bool(self.instance))
        # 4
        validated_data.update({**data})
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
            repr_['created'] = f'{obj.created:%Y-%m-%d %H:%M:%S}'
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

        1. Если происходит обновление существующего заказа, то:
        1.1 Проверяем, обновился ли плейлист. Если да, то берём
            айди плейлиста из входящих данных, а тип заказа с самого заказа
            и валидируем плейлист.
        1.2 Если же происходит создание заказа, то получаем всё из
            входящих данных и валидируем плейлист.
        2. Возвращаем валидированные данные.
        """
        def _validate_playlist(playlist_id: str, order_type: int):
            """
            Валидация плейлиста.

            1. Находим и получаем объект плейлиста, а также его файлы.
            2. Если файлов в плейлисте нет, выбрасываем ошибку.
            3. Проходим по файлам и сверяем их тип с типом заказа.
            4. При несоответствии выбрасываем ошибку.
            """
            empty_values = Constants.empty_values
            # 1
            playlist_obj = Playlist.objects.get(id=playlist_id)
            files = playlist_obj.files.all()
            # 2
            if files in empty_values:
                raise serializers.ValidationError('Плейлист не содержит файлов')
            # 3
            for file in files:
                if file.type != order_type:
                    # 4
                    raise serializers.ValidationError(
                        f'Плейлист содержит файлы неправильного типа {file.type} != {order_type}'
                    )
        # 1
        if self.instance:
            # 1.1
            if 'playlist' in self.initial_data:
                playlist_id = self.initial_data.get('playlist')
                order_type = self.instance.order_type
                _validate_playlist(playlist_id, order_type)
        # 1.2
        else:
            playlist_id = self.initial_data[0].get('playlist')
            order_type = self.initial_data[0].get('order_type')
            _validate_playlist(playlist_id, order_type)
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
            repr_['created'] = f'{obj.created:%Y-%m-%d %H:%M:%S}'
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
