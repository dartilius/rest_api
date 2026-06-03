from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('nomenclatures', '0008_discountrule'),
    ]

    operations = [
        migrations.AddField(
            model_name='nomenclature',
            name='search_vector',
            field=models.TextField(
                blank=True,
                default='',
                verbose_name='Поисковый вектор',
                help_text='Денормализованное поле для полнотекстового поиска',
            ),
        ),
        migrations.AddIndex(
            model_name='nomenclature',
            index=models.Index(
                fields=['search_vector'],
                name='nomenclatur_search__index',
            ),
        ),
    ]
