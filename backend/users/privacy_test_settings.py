"""Offline-only SQLite adapter for PostgreSQL arrays; no live migrations/services."""
from corporate_broadcast.test_settings import *  # noqa: F403
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField

# SQLite substitutes JSON only in this test settings module. Production is unaffected.
ArrayField.db_type = lambda self, connection: 'text'
ArrayField.cast_db_type = lambda self, connection: 'text'
ArrayField.get_placeholder = lambda self, value, compiler, connection: '%s'
ArrayField.get_db_prep_value = JSONField.get_db_prep_value
ArrayField.from_db_value = JSONField.from_db_value
ArrayField.encoder = None
ArrayField.decoder = None

MIGRATION_MODULES = {app.split('.')[0]: None for app in INSTALLED_APPS}  # noqa: F405
MIGRATION_MODULES.update({
    'admin': None, 'auth': None, 'contenttypes': None, 'sessions': None,
    'token_blacklist': None,
})
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
DEFAULT_FROM_EMAIL = 'offline@example.test'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
CELERY_TASK_ALWAYS_EAGER = False
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'
ROOT_URLCONF = 'users.privacy_test_urls'


class OfflineRouter:
    def allow_migrate(self, db, app_label, **hints):
        return app_label != 'ch_statistic'


DATABASE_ROUTERS = ['users.privacy_test_settings.OfflineRouter']
