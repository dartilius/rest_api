from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("users", "0002_customuser_token_1c_access_and_more")]

    operations = [
        migrations.RunSQL("SET LOCAL lock_timeout = '2s'", reverse_sql=migrations.RunSQL.noop),
        migrations.CreateModel(
            name='RegistrationEmailVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=255, unique=True)),
                ('code', models.CharField(max_length=128)),
                ('expires_at', models.DateTimeField()),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Подтверждение email при регистрации',
                'verbose_name_plural': 'Подтверждения email при регистрации',
                'db_table': 'registration_email_verification',
                'indexes': [models.Index(fields=['expires_at'], name='registratio_expires_8da1f9_idx')],
            },
        ),
        migrations.RunSQL(migrations.RunSQL.noop, reverse_sql="SET LOCAL lock_timeout = '2s'"),
    ]
