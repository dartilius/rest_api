import datetime
from celery import shared_task
from celery_singleton import Singleton

from ch_statistic.models import (
    ADStat,
    MusicStat,
    VideoStat,
    ImageStat,
    TickerStat,
    BackupImageStat
)


@shared_task
def create_statistic(stat_type, nomenclature_id, stat_list):
    """Внесение статистики в базу."""
    stat_objects = []
    match stat_type:
        case 'ad':
            model = ADStat
            for stat_element in stat_list:
                stat_objects += [model(
                    client=nomenclature_id,
                    file=stat_element['file'],
                    played=stat_element['played'],
                    length=stat_element['length'],
                    ad_block=stat_element['ad_block']
                )]
        case 'music':
            model = MusicStat
        case 'video':
            model = VideoStat
        case 'image':
            model = ImageStat
        case 'ticker':
            model = TickerStat
        case _:
            model = None

    if model:
        if stat_type != 'ad':
            for stat_element in stat_list:
                stat_objects += [model(
                    client=nomenclature_id,
                    file=stat_element['file'],
                    played=stat_element['played'],
                    length=stat_element['length']
                )]
        model.objects.bulk_create(stat_objects)
        return (
            f'Добавлено {len(stat_objects)} '
            f'записей статистики {stat_type}.'
        )


@shared_task(base=Singleton)
def backup_image_stat():
    """
    Перенос записей статистики изображений в другую таблицу,
    для улучшения быстродействия ее получения.

    Фильтруем всю статистику которая старше недели
    Порционно по 1000 штук переносим в другую таблицу и удаляем записи
    В конце проверяем остались ли еще не перенесенные записи
    Переносим оставшиеся (если имеются) и возвращаем общее количество
    перенесенных записей.
    """
    now_date = datetime.datetime.now() - datetime.timedelta(days=7)
    statistics = ImageStat.objects.filter(played__lt=now_date)
    counter = global_counter = 0
    creation_list = []
    deletion_ids = []
    for item in statistics:
        deletion_ids.append(item.pop('ID'))
        creation_list.append(BackupImageStat(**item))
        counter += 1

        if counter % 1000 == 0:
            global_counter += counter
            BackupImageStat.bulk_create(creation_list)
            creation_list = []
            counter = 0
            ImageStat.objects.delete(id__in=deletion_ids)
            deletion_ids = []

    if counter:
        global_counter += counter
        BackupImageStat.bulk_create(creation_list)
        ImageStat.objects.delete(id__in=deletion_ids)

    return (
        f'Перенесли {global_counter} записей статистики изображений '
        'в таблицу бэкапов.'
    )
