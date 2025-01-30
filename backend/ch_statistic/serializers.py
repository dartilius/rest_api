from datetime import datetime as dt, timedelta as td

from rest_framework import serializers

from ch_statistic.models import (
    ADStat,
    MusicStat,
    VideoStat,
    TickerStat,
    ImageStat
)


class StatisticSerializer(serializers.Serializer):
    """Базовый класс сериализации статистики."""

    played = serializers.DateTimeField()
    length = serializers.IntegerField()

    class Meta:
        fields = (
            'length',
        )
        read_only_fields = (
            'length',
        )
        abstract = True

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['played'] = f'{value.played:%Y-%m-%d %H:%M:%S}'
        return representation


class BaseNomenclatureSerializer(StatisticSerializer):
    """Базовый класс сериализации для срезов по номенклатуре."""

    file = serializers.CharField()

    class Meta:
        fields = StatisticSerializer.Meta.fields + ('file',)
        read_only_fields = ('file',)
        abstract = True


class BaseFileSerializer(StatisticSerializer):
    """Базовый класс сериализации для срезов по файлам."""

    client = serializers.CharField()

    class Meta:
        fields = StatisticSerializer.Meta.fields + ('client',)
        read_only_fields = ('client',)
        abstract = True


class NomenclatureAdStatSerializer(
    BaseNomenclatureSerializer,
    serializers.ModelSerializer
):
    """Сериализация статистики рекламы из номенклатуры."""

    ad_block = serializers.IntegerField()

    class Meta:
        model = ADStat
        fields = BaseNomenclatureSerializer.Meta.fields + ('ad_block',)
        read_only_fields = (
                BaseNomenclatureSerializer.Meta.
                read_only_fields +
                ('ad_block',)
        )

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation.pop('played')
        ad_block = f'{td(seconds=value.ad_block)}'
        representation['ad_block'] = (
            f'{dt.strptime(ad_block, "%H:%M:%S").time()}'
        )
        return representation


class NomenclatureMusicStatSerializer(
    BaseNomenclatureSerializer,
    serializers.ModelSerializer
):
    """Сериализация статистики музыки из номенклатуры."""

    class Meta:
        model = MusicStat
        fields = BaseNomenclatureSerializer.Meta.fields
        read_only_fields = BaseNomenclatureSerializer.Meta.read_only_fields


class NomenclatureVideoStatSerializer(
    BaseNomenclatureSerializer,
    serializers.ModelSerializer
):
    """Сериализация статистики видео из номенклатуры."""

    class Meta:
        model = VideoStat
        fields = BaseNomenclatureSerializer.Meta.fields
        read_only_fields = BaseNomenclatureSerializer.Meta.read_only_fields


class NomenclatureTickerStatSerializer(
    BaseNomenclatureSerializer,
    serializers.ModelSerializer
):
    """Сериализация статистики бегущих строк из номенклатуры."""

    class Meta:
        model = TickerStat
        fields = BaseNomenclatureSerializer.Meta.fields
        read_only_fields = BaseNomenclatureSerializer.Meta.read_only_fields


class NomenclatureImageStatSerializer(
    BaseNomenclatureSerializer,
    serializers.ModelSerializer
):
    """Сериализация статистики картинок из номенклатуры."""

    class Meta:
        model = ImageStat
        fields = BaseNomenclatureSerializer.Meta.fields
        read_only_fields = BaseNomenclatureSerializer.Meta.read_only_fields


class FileAdStatSerializer(
    BaseFileSerializer,
    serializers.ModelSerializer
):
    """Сериализация статистики рекламы из файла."""

    ad_block = serializers.IntegerField()

    class Meta:
        model = ADStat
        fields = BaseFileSerializer.Meta.fields + ('ad_block',)
        read_only_fields = (
                BaseFileSerializer.Meta.
                read_only_fields +
                ('ad_block',)
        )

    def to_representation(self, value):
        representation = super().to_representation(value)
        ad_block = f'{td(seconds=value.ad_block)}'
        representation['ad_block'] = (
            f'{dt.strptime(ad_block, "%H:%M:%S").time()}'
        )
        return representation


class FileMusicStatSerializer(
    BaseFileSerializer,
    serializers.ModelSerializer
):
    """Сериализация статистики музыки из файла."""

    class Meta:
        model = MusicStat
        fields = BaseFileSerializer.Meta.fields
        read_only_fields = BaseFileSerializer.Meta.read_only_fields


class FileVideoStatSerializer(
    BaseFileSerializer,
    serializers.ModelSerializer
):
    """Сериализация статистики видео из файла."""

    class Meta:
        model = VideoStat
        fields = BaseFileSerializer.Meta.fields
        read_only_fields = BaseFileSerializer.Meta.read_only_fields


class FileTickerStatSerializer(
    BaseFileSerializer,
    serializers.ModelSerializer
):
    """Сериализация статистики бегущих строк из файла."""

    class Meta:
        model = TickerStat
        fields = BaseFileSerializer.Meta.fields
        read_only_fields = BaseFileSerializer.Meta.read_only_fields


class FileImageStatSerializer(
    BaseFileSerializer,
    serializers.ModelSerializer
):
    """Сериализация статистики картинок из файла."""

    class Meta:
        model = ImageStat
        fields = BaseFileSerializer.Meta.fields
        read_only_fields = BaseFileSerializer.Meta.read_only_fields
