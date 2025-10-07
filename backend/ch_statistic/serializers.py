from datetime import datetime as dt, timedelta as td
from rest_framework import serializers
from ch_statistic.models import (
    ADStat,
    MusicStat,
    VideoStat,
    TickerStat,
    ImageStat,
)


class StatisticSerializer(serializers.Serializer):
    """
    Базовый сериализатор для статистики.
    
    Attributes:
        played (DateTime): Время проигрывания
        length (Integer): Длительность в секундах
    """

    played = serializers.DateTimeField()
    length = serializers.IntegerField()

    class Meta:
        fields = ("played", "length")
        read_only_fields = ("played", "length")
        abstract = True

    def to_representation(self, value):
        """
        Преобразует объект статистики в словарь для сериализации.
        
        Args:
            value: Объект статистики
            
        Returns:
            dict: Сериализованные данные
        """
        representation = super().to_representation(value)
        representation["played"] = f"{value.played:%Y-%m-%d %H:%M:%S}"
        return representation


class BaseNomenclatureSerializer(StatisticSerializer):
    """
    Базовый сериализатор для срезов по номенклатуре.
    
    Attributes:
        file (str): UUID файла
    """

    file = serializers.CharField()

    class Meta:
        fields = StatisticSerializer.Meta.fields + ("file",)
        read_only_fields = fields
        abstract = True


class BaseFileSerializer(StatisticSerializer):
    """
    Базовый сериализатор для срезов по файлам.
    
    Attributes:
        client (str): UUID номенклатуры
    """

    client = serializers.CharField()

    class Meta:
        fields = StatisticSerializer.Meta.fields + ("client",)
        read_only_fields = fields
        abstract = True


class NomenclatureAdStatSerializer(BaseNomenclatureSerializer):
    """
    Сериализатор статистики рекламы для номенклатуры.
    
    Attributes:
        ad_block (str): Время рекламного блока в формате HH:MM:SS
    """

    ad_block = serializers.SerializerMethodField()

    class Meta:
        model = ADStat
        fields = BaseNomenclatureSerializer.Meta.fields + ("ad_block",)
        read_only_fields = BaseNomenclatureSerializer.Meta.read_only_fields

    def get_ad_block(self, obj) -> str:
        """
        Преобразует секунды в читаемый формат времени.
        
        Args:
            obj: Объект ADStat
            
        Returns:
            str: Время в формате HH:MM:SS
        """
        return str(td(seconds=obj.ad_block))


class NomenclatureMusicStatSerializer(BaseNomenclatureSerializer):
    """Сериализатор статистики музыки для номенклатуры."""

    class Meta:
        model = MusicStat
        fields = BaseNomenclatureSerializer.Meta.fields
        read_only_fields = BaseNomenclatureSerializer.Meta.read_only_fields


class NomenclatureVideoStatSerializer(BaseNomenclatureSerializer):
    """Сериализатор статистики видео для номенклатуры."""

    class Meta:
        model = VideoStat
        fields = BaseNomenclatureSerializer.Meta.fields
        read_only_fields = BaseNomenclatureSerializer.Meta.read_only_fields


class NomenclatureTickerStatSerializer(BaseNomenclatureSerializer):
    """Сериализатор статистики бегущих строк для номенклатуры."""

    class Meta:
        model = TickerStat
        fields = BaseNomenclatureSerializer.Meta.fields
        read_only_fields = BaseNomenclatureSerializer.Meta.read_only_fields


class NomenclatureImageStatSerializer(BaseNomenclatureSerializer):
    """Сериализатор статистики изображений для номенклатуры."""

    class Meta:
        model = ImageStat
        fields = BaseNomenclatureSerializer.Meta.fields
        read_only_fields = BaseNomenclatureSerializer.Meta.read_only_fields


class FileAdStatSerializer(BaseFileSerializer):
    """
    Сериализатор статистики рекламы для файла.
    
    Attributes:
        ad_block (str): Время рекламного блока в формате HH:MM:SS
    """

    ad_block = serializers.SerializerMethodField()

    class Meta:
        model = ADStat
        fields = BaseFileSerializer.Meta.fields + ("ad_block",)
        read_only_fields = BaseFileSerializer.Meta.read_only_fields

    def get_ad_block(self, obj) -> str:
        """
        Преобразует секунды в читаемый формат времени.
        
        Args:
            obj: Объект ADStat
            
        Returns:
            str: Время в формате HH:MM:SS
        """
        return str(td(seconds=obj.ad_block))


class FileMusicStatSerializer(BaseFileSerializer):
    """Сериализатор статистики музыки для файла."""

    class Meta:
        model = MusicStat
        fields = BaseFileSerializer.Meta.fields
        read_only_fields = BaseFileSerializer.Meta.read_only_fields


class FileVideoStatSerializer(BaseFileSerializer):
    """Сериализатор статистики видео для файла."""

    class Meta:
        model = VideoStat
        fields = BaseFileSerializer.Meta.fields
        read_only_fields = BaseFileSerializer.Meta.read_only_fields


class FileTickerStatSerializer(BaseFileSerializer):
    """Сериализатор статистики бегущих строк для файла."""

    class Meta:
        model = TickerStat
        fields = BaseFileSerializer.Meta.fields
        read_only_fields = BaseFileSerializer.Meta.read_only_fields


class FileImageStatSerializer(BaseFileSerializer):
    """Сериализатор статистики изображений для файла."""

    class Meta:
        model = ImageStat
        fields = BaseFileSerializer.Meta.fields
        read_only_fields = BaseFileSerializer.Meta.read_only_fields

