from celery import shared_task

from ch_statistic.models import (
    ADStat,
    MusicStat,
    VideoStat,
    ImageStat,
    TickerStat
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
