import ast
import json

from datetime import time
from rest_framework import serializers

from nomenclatures.models import (
    Nomenclature,
    NomenclatureGroup,
    StatusHistory,
    TIMEZONES
)


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
        """
        Валидация настроек.

        Проверяется наличие обязательных ключей worktime и default_volume,
        корректность значений этих ключей и опциональных значений custom_volume

        Пояснение к валидации пользовательских настроек громкости.
        ----------------------------------------------------------
        Пример пользовательских настроек:
        ...
        \"custom_volume\": {\"((14,),(16,))\": \"(77, 77, 77, 77)\",
                        \"((13,),(15,))\": \"(11, 11, 11, 11)\"}}"
        ...
        Разберём код по шагам:

        1.  if 'custom_volume' in j:
                for k, v in j['custom_volume'].items():
                    _validate_time(*ast.literal_eval(k))
                    _validate_volume(ast.literal_eval(v))

        2.      sorted_times = sorted((j['custom_volume']))

        3.      for curr, next_ in zip(sorted_times, sorted_times[1:]):
                    curr = ast.literal_eval(curr)[1][0]
                    next_ = ast.literal_eval(next_)[0][0]

        4.          if curr > next_:
                        raise serializers.ValidationError(
                            'Обнаружено пересечение в часах '
                            'пользовательских настроек громкости'
                        )

        1.  Сперва проверяем корректность настроек
        2.  Далее сравниваем заданные периоды времени на пересечение, для этого
            сначала сортируем периоды. В нашем примере получится:

            sorted_times = ['((13,),(15,))', '((14,),(16,))']

        3.  Теперь нужно сравнить конец предшествующего периода
            с началом следующего. Чтобы извлечь только конец периода,
            мы обращаемся ко вложенному кортежу:

            ast.literal_eval(curr)[1][0] = 15

        4.  Если конец предыдущего периода меньше начала следующего периода,
            значит есть пересечение, вызываем исключение

        Узнать больше про zip можно в официальной документации
        https://docs.python.org/3/library/functions.html#zip
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
            """Валидация натроек громкости."""
            length = 4
            if not all(isinstance(vol, int) for vol in volume):
                raise serializers.ValidationError(
                    'Громкость должна передаваться целочисленным значением'
                )
            if not all(0 <= vol <= 100 for vol in volume):
                raise serializers.ValidationError(
                    'Громкость может быть только от 0 до 100'
                )
            if len(volume) != length:
                raise serializers.ValidationError(
                    f'Значений громкости должно быть ровно {length}'
                )

        for day in value:
            j = json.loads(value[day])
            try:
                req_keys = {
                    'worktime': j['worktime'],
                    'default_volume': ast.literal_eval(j['default_volume'])
                }
            except KeyError as k:
                raise serializers.ValidationError(f'{k} не передан')
            _validate_time(req_keys['worktime'])
            _validate_volume(req_keys['default_volume'])
            if 'custom_volume' in j:
                for k, v in j['custom_volume'].items():
                    _validate_time(*ast.literal_eval(k))
                    _validate_volume(ast.literal_eval(v))
                sorted_times = sorted((j['custom_volume']))
                for curr, next_ in zip(sorted_times, sorted_times[1:]):
                    curr = ast.literal_eval(curr)[1][0]
                    next_ = ast.literal_eval(next_)[0][0]
                    if curr > next_:
                        raise serializers.ValidationError(
                            'Обнаружено пересечение в часах '
                            'пользовательских настроек громкости'
                        )
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
        representation = super().to_representation(obj)
        representation['main_info'] = {
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
        for field in representation['main_info']:
            representation.pop(field)
        for day, setting in representation['settings'].items():
            j = json.loads(setting)
            split_interval = j['worktime'].split('-')
            start = split_interval[0]
            end = split_interval[1]
            try:
                representation['settings'][day] = {
                    'worktime': (start, end),
                    'custom_volume': [(
                        f'{time(*ast.literal_eval(k)[0])} - '
                        f'{time(*ast.literal_eval(k)[1])}',
                        ast.literal_eval(v)
                    ) for k, v in j['custom_volume'].items()],
                    'default_volume': ast.literal_eval(j['default_volume'])
                }
            except KeyError:
                representation['settings'][day] = {
                    'worktime': (start, end),
                    'default_volume': ast.literal_eval(j['default_volume'])
                }
        return representation


class NomenclatureListSerializer(serializers.ModelSerializer):
    """Сериализация списка номенклатур."""

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
        queryset=Nomenclature.objects.filter(is_active=True),
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
            } for client in value.clients.filter(is_active=True)
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
        representation['clients_count'] = len(
            value.clients.filter(is_active=True)
        )
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
