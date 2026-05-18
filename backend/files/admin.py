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

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.db.models import Count
from django import forms
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import File, Playlist, Tag, TYPES, SUBTYPES, SUBTYPE_CHOICES


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

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    """Административный интерфейс управления плейлистами."""

    list_display = (
        'id', 'name', 'owner', 'files_count', 'files_preview',
        'playlist_type_icon', 'created'
    )

    search_fields = ('name',)
    raw_id_fields = ('owner', 'files')
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
            'fields': ('files',),
            'description': (
                '💡 <strong>Советы по выбору файлов:</strong><br>'
                '• Используйте <kbd>Ctrl</kbd> + клик для множественного выбора<br>'
                '• Все файлы в плейлисте должны быть одного типа<br>'
                '• Уже выбранные файлы выделены в списке'
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
        count = 0
        for playlist in queryset:
            count += playlist.files.count()
            playlist.files.clear()
        self.message_user(request, f'✅ Очищено {queryset.count()} плейлистов, удалено {count} файлов.')

    @admin.action(description='📋 Копировать выбранные плейлисты')
    def duplicate_playlist(self, request, queryset):
        created_count = 0
        for playlist in queryset:
            new_playlist = Playlist.objects.create(
                name=f'{playlist.name} (копия)',
                description=playlist.description,
                owner=request.user
            )
            new_playlist.files.set(playlist.files.all())
            created_count += 1
        self.message_user(request, f'✅ Создано {created_count} копий.')

    def save_model(self, request, obj, form, change):
        if not obj.owner:
            obj.owner = request.user
        super().save_model(request, obj, form, change)
        if 'files' in form.cleaned_data:
            obj.files.set(form.cleaned_data['files'])


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
