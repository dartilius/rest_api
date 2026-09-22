from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nomenclatures", "0010_rename_nomenclatur_search__index_nomenclatur_search__488b14_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="nomenclature",
            name="broadcast",
            field=models.BooleanField(default=False, verbose_name="Вещание"),
        ),
    ]