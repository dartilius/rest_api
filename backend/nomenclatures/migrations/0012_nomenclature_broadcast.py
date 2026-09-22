from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nomenclatures", "0011_alter_nomenclatureaddress_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="nomenclature",
            name="broadcast",
            field=models.BooleanField(default=False, verbose_name="Вещание"),
        ),
    ]
