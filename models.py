# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AdOrder(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    broadcast_interval = django.contrib.postgres.fields.DateTimeRangeField()
    parameters = models.TextField()  # This field type is a guess.
    created = models.DateTimeField()
    broadcast_type = models.SmallIntegerField()
    file = models.ForeignKey('FilesFile', models.DO_NOTHING)
    group = models.ForeignKey('Group', models.DO_NOTHING)
    owner = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True)
    slides = models.ForeignKey('FilesFile', models.DO_NOTHING, related_name='adorder_slides_set')

    class Meta:
        managed = False
        db_table = 'ad_order'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class Availability(models.Model):
    id = models.BigAutoField(primary_key=True)
    last_answer_date = models.DateTimeField()
    status = models.SmallIntegerField()
    client = models.OneToOneField('Nomenclature', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'availability'


class BgOrder(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    broadcast_interval = django.contrib.postgres.fields.DateTimeRangeField()
    parameters = models.TextField()  # This field type is a guess.
    created = models.DateTimeField()
    group = models.ForeignKey('Group', models.DO_NOTHING)
    owner = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True)
    playlist = models.ForeignKey('FilesPlaylist', models.DO_NOTHING)
    order_type = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'bg_order'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('User', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class FilesFile(models.Model):
    id = models.UUIDField(primary_key=True)
    source = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    md5hash = models.CharField(max_length=32)
    sha256hash = models.CharField(max_length=256)
    hash = models.CharField(max_length=288)
    length = models.TimeField()
    size = models.IntegerField()
    file_type = models.SmallIntegerField()
    created = models.DateTimeField()
    owner = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'files_file'


class FilesFileTag(models.Model):
    id = models.BigAutoField(primary_key=True)
    file = models.ForeignKey(FilesFile, models.DO_NOTHING)
    tag = models.ForeignKey('FilesTag', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'files_file_tag'
        unique_together = (('file', 'tag'),)


class FilesPlaylist(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created = models.DateTimeField()
    owner = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'files_playlist'


class FilesPlaylistfiles(models.Model):
    id = models.BigAutoField(primary_key=True)
    file = models.ForeignKey(FilesFile, models.DO_NOTHING)
    playlist = models.ForeignKey(FilesPlaylist, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'files_playlistfiles'


class FilesPlaylistfilesImages(models.Model):
    id = models.BigAutoField(primary_key=True)
    playlistfiles = models.ForeignKey(FilesPlaylistfiles, models.DO_NOTHING)
    file = models.ForeignKey(FilesFile, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'files_playlistfiles_images'
        unique_together = (('playlistfiles', 'file'),)


class FilesTag(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=255)

    class Meta:
        managed = False
        db_table = 'files_tag'


class Group(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created = models.DateTimeField()
    owner = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'group'


class GroupClients(models.Model):
    id = models.BigAutoField(primary_key=True)
    nomenclaturegroup = models.ForeignKey(Group, models.DO_NOTHING)
    nomenclature = models.ForeignKey('Nomenclature', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'group_clients'
        unique_together = (('nomenclaturegroup', 'nomenclature'),)


class Nomenclature(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=255)
    timezone = models.CharField(max_length=31)
    is_active = models.BooleanField()
    status = models.SmallIntegerField()
    version = models.CharField(max_length=127)
    description = models.TextField(blank=True, null=True)
    created = models.DateTimeField()
    settings = models.TextField()  # This field type is a guess.
    hw_info = models.TextField(blank=True, null=True)  # This field type is a guess.
    owner = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'nomenclature'


class StatusHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    change_time = models.DateTimeField()
    status = models.SmallIntegerField()
    client = models.ForeignKey(Nomenclature, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'status_history'


class Task(models.Model):
    id = models.UUIDField(primary_key=True)
    parameters = models.TextField(blank=True, null=True)  # This field type is a guess.
    status = models.SmallIntegerField()
    created = models.DateTimeField()
    updated = models.DateTimeField()
    client = models.ForeignKey(Nomenclature, models.DO_NOTHING)
    owner = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True)
    type = models.ForeignKey('TasksType', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'task'


class TasksType(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    order_type = models.CharField(unique=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tasks_type'


class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    is_staff = models.BooleanField()
    date_joined = models.DateTimeField()
    username = models.CharField(unique=True, max_length=150)
    last_name = models.CharField(max_length=150)
    first_name = models.CharField(max_length=150)
    middle_name = models.CharField(max_length=150, blank=True, null=True)
    role = models.CharField(max_length=32, blank=True, null=True)
    email = models.CharField(unique=True, max_length=255)
    phone_number = models.CharField(unique=True, max_length=128)
    is_active = models.BooleanField()
    created = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'user'


class UserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'user_groups'
        unique_together = (('user', 'group'),)


class UserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'user_user_permissions'
        unique_together = (('user', 'permission'),)
