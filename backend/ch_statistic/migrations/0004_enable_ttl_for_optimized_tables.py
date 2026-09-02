from django.db import migrations


TABLES = (
    'ad_stat',
    'music_stat',
    'video_stat',
    'image_stat',
    'image_stat_backup',
    'ticker_stat',
)
EXPECTED_SORTING_KEY = 'client, played, id'


def enable_ttl_for_optimized_tables(apps, schema_editor):
    """Enable tiering only for tables created with the new physical layout.

    Existing production tables use ``ORDER BY id``.  They must be moved through
    the explicit v2 rollout, so this migration intentionally leaves them
    untouched.
    """
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "SELECT name, sorting_key FROM system.tables "
            "WHERE database = currentDatabase() AND name IN %(tables)s",
            {'tables': TABLES},
        )
        tables = dict(cursor.fetchall())

    for table in TABLES:
        if tables.get(table) != EXPECTED_SORTING_KEY:
            continue
        schema_editor.execute(
            f"ALTER TABLE {table} MODIFY TTL "
            "played + INTERVAL 1 YEAR TO VOLUME 'cold'"
        )


class Migration(migrations.Migration):

    dependencies = [
        ('ch_statistic', '0003_remove_adstat_played_krasnoyarsk_and_more'),
    ]

    operations = [
        migrations.RunPython(
            enable_ttl_for_optimized_tables,
            migrations.RunPython.noop,
            hints={'clickhouse': True},
        ),
    ]
