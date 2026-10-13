from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("users", "0003_registrationemailverification")]

    operations = [
        migrations.RunSQL("SET LOCAL lock_timeout = '2s'", reverse_sql=migrations.RunSQL.noop),
        migrations.CreateModel(
            name='PasswordResetEmailVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=255, unique=True)),
                ('code', models.CharField(max_length=128)),
                ('expires_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Подтверждение сброса пароля',
                'verbose_name_plural': 'Подтверждения сброса пароля',
                'db_table': 'password_reset_email_verification',
                'indexes': [models.Index(fields=['expires_at'], name='password_re_expires_b8fff0_idx')],
            },
        ),
        migrations.RunSQL(migrations.RunSQL.noop, reverse_sql="SET LOCAL lock_timeout = '2s'"),
    ]
