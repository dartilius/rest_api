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

logger = setup_logger('nomenclatures', 'logs/nomenclatures.log')


class NomenclatureSerializer(serializers.ModelSerializer):
    """Сериализация одной номенклатуры."""

    status = serializers.SerializerMethodField()
    last_answer = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'owner',
            'name',
            'timezone',
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
            'hw_info',
            'version',
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
        representation['owner'] = (
            f'{value.owner.last_name} {value.owner.first_name}'
        )
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
        representation['created'] = value.created.strftime('%Y-%m-%d %H:%M:%S')
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

    class Meta:
        fields = (
            'id',
            'name',
            'description',
            'owner',
            'clients',
            'created'
        )
        read_only_fields = (
            'id',
            'owner',
            'created',
        )
        model = NomenclatureGroup

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['owner'] = (
            f'{value.owner.last_name} {value.owner.first_name}'
        )
        representation['clients'] = [
            {
                'id': client.id,
                'name':  client.name
            } for client in value.clients.all()
        ]
        representation['created'] = value.created.strftime('%Y-%m-%d %H:%M:%S')
        return representation


class NomenclatureGroupListSerializer(serializers.ModelSerializer):
    """Сериализация групп номенклатуры."""

    class Meta:
        fields = (
            'id',
            'name',
            'created'
        )
        read_only_fields = fields
        model = NomenclatureGroup

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['clients_count'] = len(value.clients.all())
        representation['created'] = value.created.strftime('%Y-%m-%d %H:%M:%S')
        return representation


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

