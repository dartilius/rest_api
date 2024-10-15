from datetime import time
from rest_framework import serializers

from api.logger import setup_logger
from nomenclatures.models import (
    Nomenclature,
    StatusHistory,
    TIMEZONES
)

logger = setup_logger('nom', 'nom.log')


class NomenclatureSerializer(serializers.ModelSerializer):
    """Сериализация одной номенклатуры."""

    status = serializers.SerializerMethodField()
    last_answer = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'owner',
            'name',
            'article',
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
        """
        Валидация настроек.

        Проверяется наличие обязательных ключей worktime и default_volume,
        корректность значений этих ключей и опциональных значений custom_volume
        """

        def _validate_time(interval: str) -> None:
            """Валидация промежутков времени."""
            split_interval = interval.split('-')
            if len(split_interval) != 2:
                raise serializers.ValidationError(
                    'Интервал времени должен содержать ровно два значения!'
                )
            start = list(map(int, split_interval[0].split(':')))
            end = list(map(int, split_interval[1].split(':')))
            if not time(0, 0, 0) <= time(*start) < time(*end) <= time(23, 59, 59):
                raise serializers.ValidationError(
                    'Время начала не может быть больше времени окончания '
                    'и должно быть в промежутке 00:00:00 - 23:59:59'
                )

        def _validate_volume(volume: tuple) -> None:
            """Валидация настроек громкости."""
            length = 4
            if len(volume) != length:
                raise serializers.ValidationError(
                    f'Значений громкости должно быть ровно {length}'
                )
            if not all(isinstance(vol, int) for vol in volume):
                raise serializers.ValidationError(
                    'Громкость должна передаваться целочисленным значением'
                )
            if not all(0 <= vol <= 100 for vol in volume):
                raise serializers.ValidationError(
                    'Громкость может быть только от 0 до 100'
                )

        def _validate_collision(custom_settings: dict) -> None:
            """Валидация пересечения временных отрезков для custom_volume."""
            sorted_settings = sorted(custom_settings)
            for curr, next_ in zip(sorted_settings, sorted_settings[1:]):
                split_curr = curr.split('-')
                end_curr = list(map(int, split_curr[1].split(':')))
                split_next = next_.split('-')
                start_next = list(map(int, split_next[0].split(':')))
                if time(*end_curr) > time(*start_next):
                    raise serializers.ValidationError(
                        'Обнаружено пересечение в часах '
                        'пользовательских настроек громкости'
                    )

        for day, settings in value.items():
            try:
                req_keys = {
                    'worktime': settings['worktime'],
                    'default_volume': tuple(settings['default_volume'])
                }
            except KeyError as k:
                raise serializers.ValidationError(f'{k} не передан')
            _validate_time(req_keys['worktime'])
            _validate_volume(req_keys['default_volume'])
            if 'custom_volume' in settings:
                for interval, volume in settings['custom_volume'].items():
                    _validate_time(interval)
                    _validate_volume(tuple(volume))
                _validate_collision(settings['custom_volume'])
        return value

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

    def to_representation(self, obj):
        repr_ = super().to_representation(obj)
        repr_['main_info'] = {
            'name': obj.name,
            'description': obj.description,
            'owner': f'{obj.owner.last_name} {obj.owner.first_name}',
            'timezone': TIMEZONES[obj.timezone],
            'status': self.get_status(obj),
            'last_answer': self.get_last_answer(obj),
            'version': obj.version,
            'created': obj.created.strftime('%Y-%m-%d %H:%M:%S')
        }
        # чтобы поля не дублировались
        for field in repr_['main_info']:
            repr_.pop(field)
        for day, setting in repr_['settings'].items():
            repr_['settings'][day] = {
                'worktime': setting['worktime'],
                'default_volume': setting['default_volume'],
                'custom_volume': setting['custom_volume']
                if 'custom_volume' in setting else {}
            }
        return repr_


class NomenclatureListSerializer(serializers.ModelSerializer):
    """Сериализация списка номенклатур."""

    status = serializers.SerializerMethodField()
    last_answer = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'article',
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
        repr_ = super().to_representation(value)
        repr_['timezone'] = TIMEZONES[value.timezone]
        return repr_


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
        repr_ = super().to_representation(value)
        repr_['change_time'] = value.change_time.strftime('%Y-%m-%d %H:%M:%S')
        return repr_
