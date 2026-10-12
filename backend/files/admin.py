# files/admin.py - ПОЛНЫЙ ФАЙЛ
"""
Административный интерфейс для управления файлами, плейлистами и тегами.

ОСНОВНЫЕ ВОЗМОЖНОСТИ:
───────────────────────────────────────────────────────────────────────────────
1. Файлы (FileAdmin):
   - Быстрые фильтры по типам контента в верхней части страницы
   - Фильтрация по подтипам, тегам, активности
   - Массовые действия: активация/деактивация, работа с тегами
   - Отображение технической информации (хэши, размер, длительность)

2. Плейлисты (PlaylistAdmin):
   - Отображение состава плейлиста в читаемом виде
   - Автоматическая проверка совместимости типов файлов
   - Массовые действия: очистка и копирование

3. Теги (TagAdmin):
   - Управление цветовыми метками
   - Отображение количества связанных файлов

БЫСТРЫЕ ФИЛЬТРЫ ФАЙЛОВ:
───────────────────────────────────────────────────────────────────────────────
При открытии списка файлов отображаются кнопки быстрой фильтрации:
- 📋 Все файлы
- 🎵 Фоновая музыка (type=0)
- 🎬 Фоновые видео (type=1)
- 🖼️ Фоновые картинки (type=2)
- 📢 Реклама (type=4)

Фильтры реализованы через changelist_view() и передаются в контекст шаблона.
"""

from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.db import transaction
from django.db.models import Count
from django import forms
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from .playlist_admin_forms import (
    PlaylistItemAdminForm,
    PlaylistItemInlineForm,
    PlaylistItemInlineFormSet,
    PlaylistItemVisualInlineFormSet,
    resolved_formset_items,
)
from .playlist_admin_service import (
    AdminPlaylistDeliveryError,
    clear_playlists,
    copy_playlist,
    playlist_graph_signature,
    snapshot_playlist_items,
    sync_playlist_graph,
    validate_playlist_graph_change,
)

from .models import (
    File,
    Playlist,
    PlaylistItem,
    PlaylistItemVisual,
    Tag,
    TYPES,
    SUBTYPES,
    SUBTYPE_CHOICES,
)


# ═══════════════════════════════════════════════════════════════════════════════
# ФИЛЬТРЫ
# ═══════════════════════════════════════════════════════════════════════════════

class FileSubtypeFilter(SimpleListFilter):
    """
    Фильтр файлов по подтипу.

    Позволяет отфильтровать файлы по детальной классификации.
    Подтипы используются только для информационных целей в админке.
    """
    title = 'Подтип файла'
    parameter_name = 'subtype'

    def lookups(self, request, model_admin):
        return SUBTYPE_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(subtype=self.value())
        return queryset


# ═══════════════════════════════════════════════════════════════════════════════
# ФАЙЛЫ
# ═══════════════════════════════════════════════════════════════════════════════

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    """Административный интерфейс управления файлами."""

    @admin.display(description='Продолжительность')
    def full_length(self, obj):
        try:
            return f'{obj.length:%H:%M:%S}'
        except TypeError:
            return obj.length

    @admin.display(description='Размер')
    def formatted_size(self, obj):
        if obj.size // 1024 >= 1:
            formatted_tail = obj.size % 1048576 // 1000
            return f'{obj.size // 1048576}.{formatted_tail}Mb'
        else:
            return f'{obj.size // 1024}Kb'

    @admin.display(description='Подтип')
    def subtype_display(self, obj):
        if hasattr(obj, 'subtype') and obj.subtype:
            icon = getattr(obj, 'subtype_icon', '📄')
            name = getattr(obj, 'subtype_display', obj.subtype)
            return f'{icon} {name}'
        return '—'

    @admin.display(description='Теги')
    def tags_preview(self, obj):
        tags = obj.tags.all()[:5]
        if not tags:
            return '—'
        tags_html = []
        for tag in tags:
            color = tag.color if tag.color else '#000000'
            tags_html.append(
                format_html(
                    '<span style="background-color: {}20; color: {}; padding: 2px 6px; '
                    'border-radius: 12px; font-size: 11px; margin: 2px;">{}</span>',
                    color, color, tag.name
                )
            )
        if obj.tags.count() > 5:
            tags_html.append(f'...+{obj.tags.count() - 5}')
        return mark_safe(' '.join(tags_html))

    @admin.display(description='Ссылка')
    def file_url(self, obj):
        if obj.url:
            return format_html(
                '<a href="{}" target="_blank">🔗 Открыть</a>',
                obj.url
            )
        return '—'

    list_display = (
        'id', 'name', 'owner', 'full_length', 'formatted_size',
        'subtype_display', 'tags_preview', 'is_active', 'created'
    )

    list_filter = (
        'type', FileSubtypeFilter, 'is_active', 'created', 'tags',
    )

    search_fields = ('name',)
    raw_id_fields = ('owner', 'tags')
    show_full_result_count = False

    list_per_page = 50
    actions = ['activate_files', 'deactivate_files', 'add_tag_to_files', 'remove_tag_from_files']

    readonly_fields = ('id', 'md5hash', 'sha256hash', 'hash', 'length', 'size', 'file_url', 'created')

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'owner', 'type', 'subtype', 'is_active')
        }),
        ('Файл', {
            'fields': ('source', 'file_url')
        }),
        ('Техническая информация', {
            'fields': ('id', 'md5hash', 'sha256hash', 'hash', 'length', 'size', 'created'),
            'classes': ('collapse',)
        }),
        ('Теги', {
            'fields': ('tags',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return File.objects.all().select_related('owner').prefetch_related('tags')

    def get_search_results(self, request, queryset, search_term):
        if (request.GET.get("app_label") == "files" and request.GET.get("model_name") == "playlistitemvisual"
                and request.GET.get("field_name") == "file"):
            queryset = queryset.filter(type=2, is_active=True)
        return super().get_search_results(request, queryset, search_term)

    def save_model(self, request, obj, form, change):
        obj.owner = obj.owner or request.user
        obj.save()

    def changelist_view(self, request, extra_context=None):
        """
        Добавляет быстрые фильтры по типам контента в шапку списка файлов.

        Фильтры отображаются в виде кнопок:
        - 📋 Все файлы (сбрасывает фильтр)
        - 🎵 Фоновая музыка (type=0)
        - 🎬 Фоновые видео (type=1)
        - 🖼️ Фоновые картинки (type=2)
        - 📢 Реклама (type=4)

        Активный фильтр подсвечивается.
        """
        extra_context = extra_context or {}
        current_type = request.GET.get('type__exact', '')

        extra_context['quick_filters'] = [
            {'label': '📋 Все файлы', 'query': '?', 'active': current_type == '', 'color': '#666'},
            {'label': '🎵 Фоновая музыка', 'query': '?type__exact=0', 'active': current_type == '0', 'color': '#4CAF50'},
            {'label': '🎬 Фоновые видео', 'query': '?type__exact=1', 'active': current_type == '1', 'color': '#2196F3'},
            {'label': '🖼️ Фоновые картинки', 'query': '?type__exact=2', 'active': current_type == '2',
             'color': '#FF9800'},
            {'label': '📢 Реклама', 'query': '?type__exact=4', 'active': current_type == '4', 'color': '#F44336'},
        ]

        return super().changelist_view(request, extra_context=extra_context)

    @admin.action(description='✅ Активировать выбранные файлы')
    def activate_files(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'✅ Активировано {updated} файлов.')

    @admin.action(description='🗑️ Деактивировать выбранные файлы')
    def deactivate_files(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'🗑️ Деактивировано {updated} файлов.')

    @admin.action(description='➕ Добавить тег к выбранным файлам')
    def add_tag_to_files(self, request, queryset):
        class TagSelectForm(forms.Form):
            tag = forms.ModelChoiceField(queryset=Tag.objects.all(), label='Выберите тег')

        if 'apply' in request.POST:
            form = TagSelectForm(request.POST)
            if form.is_valid():
                tag = form.cleaned_data['tag']
                count = 0
                for file in queryset:
                    file.tags.add(tag)
                    count += 1
                self.message_user(request, f'✅ Тег "{tag.name}" добавлен к {count} файлам.')
                return
        else:
            form = TagSelectForm()

        return self.render_changeform(request, {
            'title': 'Добавить тег к файлам',
            'form': form,
            'queryset': queryset,
            'action': 'add_tag_to_files',
        })

    @admin.action(description='❌ Удалить тег из выбранных файлов')
    def remove_tag_from_files(self, request, queryset):
        class TagSelectForm(forms.Form):
            tag = forms.ModelChoiceField(queryset=Tag.objects.all(), label='Выберите тег')

        if 'apply' in request.POST:
            form = TagSelectForm(request.POST)
            if form.is_valid():
                tag = form.cleaned_data['tag']
                count = 0
                for file in queryset:
                    file.tags.remove(tag)
                    count += 1
                self.message_user(request, f'✅ Тег "{tag.name}" удален из {count} файлов.')
                return
        else:
            form = TagSelectForm()

        return self.render_changeform(request, {
            'title': 'Удалить тег из файлов',
            'form': form,
            'queryset': queryset,
            'action': 'remove_tag_from_files',
        })


# ═══════════════════════════════════════════════════════════════════════════════
# ПЛЕЙЛИСТЫ
# ═══════════════════════════════════════════════════════════════════════════════

class PlaylistAdminForm(forms.ModelForm):
    """Adds many new playlist files without exposing already selected ones."""

    files_to_add = forms.ModelMultipleChoiceField(
        queryset=File.objects.none(),
        required=False,
        label="Добавить файлы",
        help_text="Можно выбрать несколько файлов. Уже добавленные файлы в список не попадают.",
        widget=forms.SelectMultiple(attrs={"size": 14}),
    )

    class Meta:
        model = Playlist
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        selected_ids = set()
        if self.instance.pk:
            selected_ids.update(self.instance.files.values_list("pk", flat=True))
            selected_ids.update(self.instance.items.values_list("file_id", flat=True))
        self.fields["files_to_add"].queryset = File.objects.filter(
            is_active=True
        ).exclude(pk__in=selected_ids).order_by("name")

    def clean(self):
        data = super().clean()
        additions = data.get("files_to_add")
        if self.instance.pk and additions:
            try:
                validate_playlist_graph_change(self.instance)
            except ValidationError as exc:
                self.add_error("files_to_add", exc)
        return data


class PlaylistItemInline(admin.TabularInline):
    model = PlaylistItem
    form = PlaylistItemInlineForm
    formset = PlaylistItemInlineFormSet
    extra = 0
    fields = ("position", "file", "images")
    ordering = ("position",)
    autocomplete_fields = ("file",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("file", "playlist").prefetch_related("visuals")


class PlaylistItemVisualInline(admin.TabularInline):
    model = PlaylistItemVisual
    formset = PlaylistItemVisualInlineFormSet
    extra = 0
    fields = ("position", "file")
    ordering = ("position",)
    raw_id_fields = ("file",)


@admin.register(PlaylistItem)
class PlaylistItemAdmin(admin.ModelAdmin):
    list_display = ("playlist", "position", "file")
    form = PlaylistItemAdminForm
    exclude = ("weight",)
    list_select_related = ("playlist", "file")
    raw_id_fields = ("playlist", "file")
    inlines = (PlaylistItemVisualInline,)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        try:
            return super().changeform_view(request, object_id, form_url, extra_context)
        except AdminPlaylistDeliveryError as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
            return HttpResponseRedirect(request.path)

    def changelist_view(self, request, extra_context=None):
        try:
            return super().changelist_view(request, extra_context)
        except AdminPlaylistDeliveryError as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
            return HttpResponseRedirect(request.path)

    def delete_view(self, request, object_id, extra_context=None):
        try:
            return super().delete_view(request, object_id, extra_context)
        except AdminPlaylistDeliveryError as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
            return HttpResponseRedirect(
                reverse("admin:files_playlistitem_change", args=(object_id,))
            )

    def save_model(self, request, obj, form, change):
        original = (
            PlaylistItem.objects.select_related("playlist").get(pk=obj.pk)
            if change
            else None
        )
        playlist_ids = {obj.playlist_id}
        if original is not None:
            playlist_ids.add(original.playlist_id)
        states = {}
        for playlist in Playlist.objects.select_for_update(no_key=True).filter(
            pk__in=playlist_ids
        ).order_by("pk"):
            states[playlist.pk] = {
                "signature": playlist_graph_signature(playlist),
                "items": snapshot_playlist_items(playlist),
            }
        request._playlist_item_graph_states = states
        request._playlist_item_source_id = (
            original.playlist_id if original is not None else None
        )
        request._playlist_item_desired_position = obj.position

        occupied = set(
            PlaylistItem.objects.filter(playlist_id=obj.playlist_id)
            .exclude(pk=obj.pk)
            .values_list("position", flat=True)
        )
        if obj.position in occupied:
            candidate = 0
            forbidden = occupied | {obj.position}
            while candidate in forbidden:
                candidate += 1
            obj.position = candidate
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        item = form.instance
        source_id = getattr(request, "_playlist_item_source_id", None)
        states = getattr(request, "_playlist_item_graph_states", {})
        desired_position = getattr(
            request, "_playlist_item_desired_position", item.position
        )
        for playlist_id in sorted({item.playlist_id, source_id} - {None}, key=str):
            playlist = Playlist.objects.get(pk=playlist_id)
            state = states[playlist_id]
            if playlist_id == item.playlist_id and state["signature"][0] == "files":
                desired = list(state["items"])
                desired = [row for row in desired if row["file"].pk != item.file_id]
                visuals = list(
                    item.visuals.select_related("file").order_by("position", "pk")
                )
                desired.append(
                    {
                        "file": item.file,
                        "images": [visual.file for visual in visuals],
                        "position": desired_position,
                    }
                )
            else:
                desired = snapshot_playlist_items(playlist)
                if state["signature"][0] == "items" and not playlist.items.exists():
                    desired = []
                for row in desired:
                    if row["file"].pk == item.file_id and playlist_id == item.playlist_id:
                        row["position"] = desired_position
            desired.sort(key=lambda row: row["position"])
            sync_playlist_graph(
                playlist,
                desired,
                previous_signature=state["signature"],
            )

    @staticmethod
    def _delete_plan(queryset):
        if not hasattr(queryset, "select_related"):
            queryset = PlaylistItem.objects.filter(
                pk__in=[item.pk for item in queryset]
            )
        selected = list(queryset.select_related("playlist"))
        selected_ids = {item.pk for item in selected}
        playlists = {
            item.playlist_id: item.playlist
            for item in selected
        }
        plan = {}
        for playlist_id, playlist in playlists.items():
            before = playlist_graph_signature(playlist)
            desired = [
                row
                for item, row in zip(
                    playlist.items.order_by("position", "pk"),
                    snapshot_playlist_items(playlist),
                )
                if item.pk not in selected_ids
            ]
            plan[playlist_id] = (playlist, before, desired)
        return plan

    def get_deleted_objects(self, objs, request):
        result = list(super().get_deleted_objects(objs, request))
        try:
            for playlist, _, desired in self._delete_plan(objs).values():
                validate_playlist_graph_change(
                    playlist,
                    will_be_empty=not desired,
                )
        except ValidationError as exc:
            result[3].extend(exc.messages)
        return tuple(result)

    def log_deletions(self, request, queryset):
        # Default delete_selected logs before mutation. Delay it so a failed
        # graph/delivery transaction never leaves a false audit record.
        request._playlist_item_deletion_log = list(queryset)

    def delete_queryset(self, request, queryset):
        with transaction.atomic():
            plan = self._delete_plan(queryset)
            for playlist, before, desired in plan.values():
                sync_playlist_graph(
                    playlist,
                    desired,
                    previous_signature=before,
                )
            pending = getattr(request, "_playlist_item_deletion_log", ())
            if pending:
                super().log_deletions(request, pending)

    def delete_model(self, request, obj):
        with transaction.atomic():
            plan = self._delete_plan(PlaylistItem.objects.filter(pk=obj.pk))
            for playlist, before, desired in plan.values():
                sync_playlist_graph(
                    playlist,
                    desired,
                    previous_signature=before,
                )
            pending = getattr(request, "_playlist_item_deletion_log", ())
            if pending:
                super().log_deletions(request, pending)


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    """Административный интерфейс управления плейлистами."""

    inlines = (PlaylistItemInline,)
    form = PlaylistAdminForm

    class Media:
        js = ("files/playlist_images.js",)

    list_display = (
        'id', 'name', 'owner', 'files_count', 'files_preview',
        'playlist_type_icon', 'created'
    )

    search_fields = ('name',)
    raw_id_fields = ('owner',)
    show_full_result_count = False

    list_per_page = 50
    filter_horizontal = ('files',)
    actions = ['clear_playlist', 'duplicate_playlist']

    readonly_fields = ('id', 'created', 'playlist_composition')

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'owner', 'id')
        }),
        ('Файлы плейлиста', {
            'fields': ('files_to_add',),
            'description': (
                '💡 <strong>Добавьте один или несколько новых файлов.</strong><br>'
                'Уже добавленные файлы исключены из списка. Для удаления или изменения '
                'состава используйте таблицу «Элементы плейлиста» ниже. '
                'Для рекламы: добавьте аудио в строку и выберите его картинки '
                'в колонке «Картинки к этому аудио». Время показа задавать не нужно.'
            )
        }),
        ('📊 Состав плейлиста', {
            'fields': ('playlist_composition',),
            'description': 'Отображает статистику по типам файлов в плейлисте'
        }),
        ('Системная информация', {
            'fields': ('created',),
            'classes': ('collapse',)
        }),
    )

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        try:
            return super().changeform_view(request, object_id, form_url, extra_context)
        except AdminPlaylistDeliveryError as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
            return HttpResponseRedirect(request.path)

    def get_queryset(self, request):
        return Playlist.objects.all().select_related('owner').prefetch_related(
            'files', 'files__tags'
        ).annotate(_files_count=Count('files'))

    @admin.display(description='Файлов')
    def files_count(self, obj):
        count = getattr(obj, '_files_count', obj.files.count())
        return f'📁 {count}' if count > 0 else '📁 0'

    @admin.display(description='Файлы')
    def files_preview(self, obj):
        files = obj.files.all()[:5]
        if not files:
            return '—'
        preview_html = []
        for file in files:
            type_icon = {0: '🎵', 1: '🎬', 2: '🖼️', 3: '📜', 4: '📢'}.get(file.type, '📄')
            file_url = reverse('admin:files_file_change', args=[file.id])
            name = file.name[:20] + '...' if len(file.name) > 20 else file.name
            preview_html.append(
                format_html(
                    '<a href="{}" title="{}" style="text-decoration:none;margin-right:8px;">{} {}</a>',
                    file_url, file.name, type_icon, name
                )
            )
        if obj.files.count() > 5:
            preview_html.append(f'...+{obj.files.count() - 5}')
        return mark_safe(' '.join(preview_html))

    @admin.display(description='Тип')
    def playlist_type_icon(self, obj):
        first_file = obj.files.first()
        if not first_file:
            return '❓ Пустой'
        type_info = {
            0: ('🎵 Музыкальный', '#4CAF50'),
            1: ('🎬 Видео', '#2196F3'),
            2: ('🖼️ Изображения', '#FF9800'),
            4: ('📢 Рекламный', '#F44336'),
        }
        type_name, color = type_info.get(first_file.type, ('❓ Смешанный', '#999'))
        types = set(obj.files.values_list('type', flat=True).distinct())
        if len(types) > 1:
            return format_html('<span style="color:#FF9800;">⚠️ Смешанный</span>')
        return format_html('<span style="color:{};">{}</span>', color, type_name)

    def playlist_composition(self, obj):
        files = obj.files.all()
        if not files:
            return '📭 Плейлист пуст'
        composition = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        for file in files:
            composition[file.type] = composition.get(file.type, 0) + 1
        type_names = {
            0: ('🎵 Музыка', '#4CAF50'),
            1: ('🎬 Видео', '#2196F3'),
            2: ('🖼️ Изображения', '#FF9800'),
            3: ('📜 Бегущая строка', '#9C27B0'),
            4: ('📢 Реклама', '#F44336'),
        }
        html = ['<div style="display:flex;gap:15px;flex-wrap:wrap;">']
        for type_id, count in composition.items():
            if count > 0:
                name, color = type_names.get(type_id, ('❓ Другое', '#999'))
                html.append(
                    f'<div style="background:{color}10;padding:8px 12px;border-radius:8px;'
                    f'border-left:3px solid {color};">'
                    f'<strong>{name}</strong> <span style="color:#666;">{count} шт</span>'
                    f'</div>'
                )
        html.append('</div>')
        return mark_safe(''.join(html))

    @admin.action(description='🗑️ Очистить выбранные плейлисты')
    def clear_playlist(self, request, queryset):
        playlists = list(queryset)
        try:
            removed = clear_playlists(playlists)
        except (ValidationError, AdminPlaylistDeliveryError) as exc:
            text = " ".join(exc.messages) if isinstance(exc, ValidationError) else str(exc)
            self.message_user(request, text, level=messages.ERROR)
            return
        self.message_user(
            request,
            f'✅ Очищено {len(playlists)} плейлистов, удалено {removed} файлов.',
        )

    @admin.action(description='📋 Копировать выбранные плейлисты')
    def duplicate_playlist(self, request, queryset):
        if not self.has_add_permission(request):
            self.message_user(
                request,
                "Недостаточно прав для создания копии плейлиста.",
                level=messages.ERROR,
            )
            return
        playlists = list(queryset)
        with transaction.atomic():
            for playlist in playlists:
                copy_playlist(playlist, owner=request.user)
        self.message_user(request, f'✅ Создано {len(playlists)} копий.')

    def save_model(self, request, obj, form, change):
        if not obj.owner:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        form.save_m2m()
        selected_files = list(form.cleaned_data.get("files_to_add") or ())
        item_formset = next(
            (formset for formset in formsets if formset.model is PlaylistItem),
            None,
        )
        if item_formset is not None:
            # Django's admin change log reads these collections after
            # ``save_related``. Build them without letting the formset write
            # rows independently from the atomic graph service.
            item_formset.save(commit=False)
            desired = resolved_formset_items(item_formset)
            has_structured_graph = form.instance.items.exists() or bool(desired)
            if not has_structured_graph and selected_files:
                desired = snapshot_playlist_items(form.instance)
            seen = {item["file"].pk for item in desired}
            next_position = max(
                (item["position"] for item in desired),
                default=-1,
            ) + 1
            desired.extend(
                {
                    "file": file,
                    "images": [],
                    "position": next_position + index,
                }
                for index, file in enumerate(selected_files)
                if file.pk not in seen
            )
            if has_structured_graph or selected_files:
                sync_playlist_graph(form.instance, desired)
        for formset in formsets:
            if formset is not item_formset:
                self.save_formset(request, form, formset, change=change)

    def save_formset(self, request, form, formset, change):
        if formset.model is not PlaylistItem:
            return super().save_formset(request, form, formset, change)
        formset.save(commit=False)
        desired = resolved_formset_items(formset)
        if not form.instance.items.exists() and not desired:
            return
        sync_playlist_graph(form.instance, desired)


# ═══════════════════════════════════════════════════════════════════════════════
# ТЕГИ
# ═══════════════════════════════════════════════════════════════════════════════

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Административный интерфейс управления тегами."""

    list_display = ('id', 'name', 'color', 'files_count')
    show_full_result_count = False

    @admin.display(description='Файлов')
    def files_count(self, obj):
        return obj.files.count()

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(files_count=Count('files'))
