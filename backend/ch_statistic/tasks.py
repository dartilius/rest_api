import datetime
from celery import shared_task
from celery_singleton import Singleton
from django.db import transaction
from django.core.cache import cache
from ch_statistic.models import (
    ADStat,
    MusicStat,
    VideoStat,
    ImageStat,
    TickerStat,
    BackupImageStat
)

# Константы для кэширования
STAT_CACHE_TIMEOUT = 3600  # 1 час
BATCH_SIZE = 1000  # Размер батча для bulk операций


@shared_task
def create_statistic(stat_type, nomenclature_id, stat_list):
    """
    Создание записей статистики в базе данных ClickHouse.
    
    Args:
        stat_type (str): Тип статистики ('ad', 'music', 'video', 'image', 'ticker')
        nomenclature_id (str): UUID номенклатуры
        stat_list (list): Список словарей с данными статистики
        
    Returns:
        str: Сообщение о результате операции
    """
    if not stat_list:
        return f"Пустой список статистики для типа {stat_type}"
    
    # Определяем модель по типу статистики
    model_map = {
        'ad': ADStat,
        'music': MusicStat,
        'video': VideoStat,
        'image': ImageStat,
        'ticker': TickerStat
    }
    
    model = model_map.get(stat_type)
    if not model:
        return f"Неизвестный тип статистики: {stat_type}"
    
    # Подготавливаем объекты для массового создания
    stat_objects = []
    
    try:
        if stat_type == 'ad':
            for stat_element in stat_list:
                stat_objects.append(model(
                    client=nomenclature_id,
                    file=stat_element['file'],
                    played=stat_element['played'],
                    length=stat_element['length'],
                    ad_block=stat_element['ad_block']
                ))
        else:
            for stat_element in stat_list:
                stat_objects.append(model(
                    client=nomenclature_id,
                    file=stat_element['file'],
                    played=stat_element['played'],
                    length=stat_element['length']
                ))
        
        # Массовое создание записей
        if stat_objects:
            model.objects.bulk_create(stat_objects, batch_size=BATCH_SIZE)
            
            # Инвалидируем кэш статистики
            cache.delete_pattern(f'stat_*_{nomenclature_id}_*')
            
            return (
                f'Добавлено {len(stat_objects)} '
                f'записей статистики {stat_type} для номенклатуры {nomenclature_id}.'
            )
        else:
            return "Нет данных для сохранения"
            
    except Exception as e:
        # Логирование ошибки
        return f"Ошибка при сохранении статистики {stat_type}: {str(e)}"


@shared_task(base=Singleton)
def backup_image_stat():
    """
    Перенос устаревших записей статистики изображений в таблицу бэкапа.
    
    Фильтрует статистику старше 7 дней и порционно переносит в backup таблицу
    для улучшения производительности основных запросов.
    
    Returns:
        str: Сообщение о количестве перенесенных записей
    """
    try:
        # Определяем дату фильтрации (старее 7 дней)
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=7)
        
        # Получаем записи для переноса
        statistics = ImageStat.objects.filter(played__lt=cutoff_date)
        total_count = statistics.count()
        
        if total_count == 0:
            return "Нет записей для переноса в бэкап"
        
        # Порционный перенос данных
        transferred_count = 0
        batch_size = BATCH_SIZE
        
        for i in range(0, total_count, batch_size):
            # Получаем батч записей
            batch = statistics[i:i + batch_size]
            
            # Создаем объекты для бэкапа
            backup_objects = []
            for item in batch:
                backup_objects.append(BackupImageStat(
                    created=item.created,
                    played=item.played,
                    file=item.file,
                    client=item.client,
                    length=item.length
                ))
            
            # Массовое создание в бэкапе и удаление из основной таблицы
            if backup_objects:
                BackupImageStat.objects.bulk_create(backup_objects)
                # Удаляем перенесенные записи
                ImageStat.objects.filter(
                    played__in=[item.played for item in batch],
                    file__in=[item.file for item in batch],
                    client__in=[item.client for item in batch]
                ).delete()
                
                transferred_count += len(backup_objects)
        
        # Инвалидируем кэш
        cache.delete_pattern('image_stat_*')
        
        return (
            f'Перенесено {transferred_count} записей статистики изображений '
            f'в таблицу бэкапов. Осталось: {total_count - transferred_count}'
        )
        
    except Exception as e:
        return f"Ошибка при переносе статистики в бэкап: {str(e)}"


@shared_task
def cleanup_old_statistics(days=90):
    """
    Очистка очень старой статистики из бэкап таблицы.
    
    Args:
        days (int): Количество дней для хранения (по умолчанию 30)
        
    Returns:
        str: Сообщение о результате очистки
    """
    try:
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        deleted_count = BackupImageStat.objects.filter(
            played__lt=cutoff_date
        ).delete()
        
        return f"Удалено {deleted_count} устаревших записей из бэкапа"
        
    except Exception as e:
        return f"Ошибка при очистке устаревшей статистики: {str(e)}"
