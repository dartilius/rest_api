import ast
import json

from datetime import time
from rest_framework import serializers

from api.logger import setup_logger

from nomenclatures.models import (
    Nomenclature,
    NomenclatureGroup,
    TIMEZONES, StatusHistory
)

logger = setup_logger('nomenclatures', '..nomenclatures.log')


class NomenclatureSerializer(serializers.ModelSerializer):
    """Сериализация одной номенклатуры."""

    owner = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    last_answer = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'owner',
            'name',
            'timezone',
            'is_active',
            'status',
            'last_answer',
            'version',
            'description',
            'settings',
            'hw_info',
            'created'
        )
        read_only_fields = (
            'id',
            'owner',
            'is_active',
            'hw_info',
            'created',
            'status',
            'last_answer'
        )
        model = Nomenclature

    def validate_settings(self, value):
        """Валидация настроек."""
        def __validate_time(*args) -> None:
            if len(args) != 2:
                raise serializers.ValidationError(
                    'Аргумент времени должен содержать ровно два значения'
                )
            try:
                start = time(*args[0])
                end = time(*args[1])
            except Exception as e:
                logger.exception(f'Возникла ошибка: {e}')
                raise serializers.ValidationError(e)
            if not time(0, 0, 0) <= start < end <= time(23, 59, 59):
                raise serializers.ValidationError(
                    'Неправильно задан интервал времени'
                )

        def __validate_volume(volume: tuple) -> None:
            length = 4
            if not all(isinstance(vol, int) for vol in volume):
                raise serializers.ValidationError(
                    'Громкость должна передаваться целочисленным значением'
                )
            if not all(0 <= vol <= 100 for vol in volume):
                raise serializers.ValidationError(
                    'Громкость может быть только от 0 до 100'
                )
            if len(volume) != 4:
                raise serializers.ValidationError(
                    f'Значений громкости должно быть ровно {length}'
                )

        for day in value:
            j = json.loads(value[day])
            try:
                req_keys = {
                    'worktime': ast.literal_eval(j['worktime']),
                    'default_volume': ast.literal_eval(j['default_volume'])
                }
                for key in req_keys:
                    if key not in j:
                        raise serializers.ValidationError(
                            f'{key} не передан'
                        )
                    if not isinstance(req_keys[key], tuple):
                        raise serializers.ValidationError(
                            'Не правильный формат данных'
                        )
                __validate_time(*req_keys['worktime'])
                __validate_volume(req_keys['default_volume'])
                if 'custom_volume' in day:
                    sorted_times = sorted(day['custom_volume'].keys())
                    for i in sorted_times:
                        if i[1][0] < i[0][1]:
                            raise serializers.ValidationError(
                                'Обнаружено пересечение в часах '
                                'пользовательских настроек громкости'
                            )
                    for k, v in day['custom_volume']:
                        __validate_time(*ast.literal_eval(k))
                        __validate_volume(ast.literal_eval(v))
            except Exception as e:
                logger.exception(f'Возникла ошибка: {e}')
                raise serializers.ValidationError(e)
        return value

    def validate_hw_info(self, value):
        """Валидирование информации о железе."""

        def __validate_config(config: dict, keys: dict, validate_func) -> None:
            try:
                for key, val in keys.items():
                    if key not in config:
                        raise serializers.ValidationError(f'{key} не передан')
                    if not isinstance(ast.literal_eval(config[key]), val):
                        raise serializers.ValidationError(
                            f'Не верный тип параметра {key}'
                        )
            except Exception as e:
                logger.exception(f'Возникла ошибка: {e}')
                raise serializers.ValidationError(e)
            validate_func(config)

        def __validate_network_config(config: dict) -> None:
            ip_length = 4
            mac_length = 6
            if len(config['ip'].split('.')) != ip_length:
                raise serializers.ValidationError('Не верный формат IP адрес')
            if len(config['mac'].split(':')) != mac_length:
                raise serializers.ValidationError('Не верный формат MAC адрес')

        def __validate_audio_devices(device: dict) -> None:
            possible_devices = ['default', 'Headphone', 'Speaker', 'HDMI']
            if not isinstance(device['card_number'], int):
                raise serializers.ValidationError(
                    'Номер звуковой карты должен быть числом'
                )
            if device['card_item'] not in possible_devices:
                raise serializers.ValidationError(
                    'Звуковой карты нет в списке допустимых'
                )

        for config_type in ['network_config', 'audio_devices']:
            for i in range(len(value[config_type])):
                config_data = json.loads(value[config_type][i])
                if config_type == 'network_config':
                    validate_keys = {'name': str, 'mac': str, 'ip': str}
                    validate_func = __validate_network_config
                else:
                    validate_keys = {'card_number': int, 'card_item': str}
                    validate_func = __validate_audio_devices
                __validate_config(config_data, validate_keys, validate_func)

    def get_owner(self, obj):
        return f'{obj.owner.last_name} {obj.owner.first_name}'

    def get_status(self, obj):
        try:
            return obj.availability.status
        except Exception:
            return None

    def get_last_answer(self, obj):
        try:
            return obj.availability.last_answer_date.strftime(
                '%Y-%m-%d %H:%M:%S'
            )
        except Exception:
            return 'Не выходила в сеть'

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['timezone'] = TIMEZONES[value.timezone]
        for day, setting in representation['settings'].items():
            j = json.loads(setting)
            to_literal = ast.literal_eval(j['worktime'])
            start = time(*to_literal[0]).strftime('%H:%M:%S')
            end = time(*to_literal[1]).strftime('%H:%M:%S')
            try:
                representation['settings'][day] = {
                    'worktime': (start, end),
                    'custom_volume': ast.literal_eval(j['custom_volume']),
                    'default_volume': ast.literal_eval(j['default_volume'])
                }
            except KeyError:
                representation['settings'][day] = {
                    'worktime': (start, end),
                    'default_volume': ast.literal_eval(j['default_volume'])
                }
        return representation


class NomenclatureListSerializer(serializers.ModelSerializer):
    """Сериализация всех номенклатур."""

    status = serializers.SerializerMethodField()
    last_answer = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'name',
            'timezone',
            'status',
            'last_answer',
            'version'
        )
        read_only_fields = fields
        model = Nomenclature

    def get_status(self, obj):
        try:
            return obj.availability.status
        except AttributeError:
            return None

    def get_last_answer(self, obj):
        try:
            return obj.availability.last_answer_date.strftime(
                '%Y-%m-%d %H:%M:%S'
            )
        except AttributeError:
            return 'Не выходила в сеть'

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['timezone'] = TIMEZONES[value.timezone]
        return representation


class NomenclatureGroupSerializer(serializers.ModelSerializer):
    """Сериализация групп номенклатуры."""

    clients = serializers.SlugRelatedField(
        slug_field='id',
        many=True,
        queryset=Nomenclature.objects.all(),
        write_only=True
    )
    owner = serializers.SerializerMethodField()
    clients_info = serializers.SerializerMethodField()

    def get_owner(self, obj):
        return f'{obj.owner.last_name} {obj.owner.first_name}'

    def get_clients_info(self, obj):
        return [
            {
                'id': client.id, 'name': client.name
            } for client in obj.clients.all()
        ]

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['created'] = value.created.strftime('%Y-%m-%d %H:%M:%S')
        return representation

    class Meta:
        fields = (
            'clients',
            'clients_info',
            'owner',
            'name',
            'description',
            'created'
        )
        read_only_fields = (
            'owner',
            'created',
            'clients_info'
        )
        model = NomenclatureGroup


class StatusHistorySerializer(serializers.ModelSerializer):
    """Сериализация истории доступности."""

    class Meta:
        fields = (
            'change_time',
            'status'
        )
        read_only_fields = fields
        model = StatusHistory

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['change_time'] = value.change_time.strftime(
            '%Y-%m-%d %H:%M:%S'
        )
        return representation

