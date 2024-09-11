from rest_framework import serializers

from ch_statistic.models import ADStat, MusicStat, VideoStat, TickerStat, ImageStat
from files.models import File
from nomenclatures.models import Nomenclature


class StatisticSerializer(serializers.Serializer):
    """Базовый класс сериализации статистики."""

    client = serializers.CharField()
    value = serializers.CharField()
    played = serializers.DateTimeField()
    length = serializers.IntegerField()
    created = serializers.DateTimeField()

    class Meta:
        fields = (
            'client',
            'value',
            'played',
            'length',
            'created'
        )
        read_only_fields = (
            'client',
            'value',
            'played',
            'length',
            'created'
        )
        abstract = True

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['created'] = value.created.strftime('%Y-%m-%d %H:%M:%S')
        representation['played'] = value.played.strftime('%Y-%m-%d %H:%M:%S')
        return representation


class AdStatSerializer(StatisticSerializer):
    """Сериализация статистики рекламы."""

    ad_block = serializers.IntegerField()

    class Meta:
        fields = StatisticSerializer.Meta.fields + ('ad_block',)
        read_only_fields = (
                StatisticSerializer.Meta.
                read_only_fields +
                ('ad_block',)
        )


class MusicStatSerializer(StatisticSerializer, serializers.ModelSerializer):
    """Сериализация статистики музыки."""

    class Meta:
        model = MusicStat
        fields = StatisticSerializer.Meta.fields
        read_only_fields = StatisticSerializer.Meta.read_only_fields


class VideoStatSerializer(StatisticSerializer, serializers.ModelSerializer):
    """Сериализация статистики видео."""

    class Meta:
        model = VideoStat
        fields = StatisticSerializer.Meta.fields
        read_only_fields = StatisticSerializer.Meta.read_only_fields


class TickerStatSerializer(StatisticSerializer, serializers.ModelSerializer):
    """Сериализация статистики бегущих строк."""

    class Meta:
        model = TickerStat
        fields = StatisticSerializer.Meta.fields
        read_only_fields = StatisticSerializer.Meta.read_only_fields


class ImageStatSerializer(StatisticSerializer, serializers.ModelSerializer):
    """Сериализация статистики картинок."""

    class Meta:
        model = ImageStat
        fields = StatisticSerializer.Meta.fields
        read_only_fields = StatisticSerializer.Meta.read_only_fields
