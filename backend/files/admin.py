from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.db.models import Count
from django import forms
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import File, Playlist, Tag, TYPES, SUBTYPES, SUBTYPE_CHOICES


# ====================================================================================
# НОВЫЕ ОПТИМИЗИРОВАННЫЕ ФИЛЬТРЫ
# ====================================================================================

class FileSubtypeFilter(SimpleListFilter):
    """Фильтр по подтипу файла"""
    title = 'Подтип файла'
    parameter_name = 'subtype'
    
    def lookups(self, request, model_admin):
        return SUBTYPE_CHOICES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(subtype=self.value())
        return queryset


# ====================================================================================
# FileAdmin - ПОЛНАЯ ОПТИМИЗАЦИЯ (сохраняем все существующие методы)
# ====================================================================================

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    """Файл."""

    # ✅ СУЩЕСТВУЮЩИЕ МЕТОДЫ (НЕ ТРОГАЕМ)
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

    # ✅ СУЩЕСТВУЮЩИЕ ПОЛЯ + НОВЫЕ (добавляем, не удаляем)
    list_display = (
        'id',
        'name',
        'owner',
        'full_length',
        'formatted_size',
        'subtype_display',      # НОВОЕ (опционально)
        'tags_preview',          # НОВОЕ (улучшение)
        'is_active',
        'created'
    )
    
    # ✅ СУЩЕСТВУЮЩИЕ ПОЛЯ + НОВЫЕ ФИЛЬТРЫ
    list_filter = (
        'type',                  # СУЩЕСТВУЮЩЕЕ
        FileSubtypeFilter,       # НОВОЕ
        'is_active',             # СУЩЕСТВУЮЩЕЕ
        'created',               # СУЩЕСТВУЮЩЕЕ
        'tags',                  # СУЩЕСТВУЮЩЕЕ
    )
    
    # ✅ СУЩЕСТВУЮЩИЕ НАСТРОЙКИ
    search_fields = ('name',)
    raw_id_fields = ('owner', 'tags')
    show_full_result_count = False
    
    # ✅ НОВЫЕ НАСТРОЙКИ (улучшения)
    list_per_page = 50
    actions = ['activate_files', 'deactivate_files', 'add_tag_to_files', 'remove_tag_from_files']
    
    # ✅ ДОБАВЛЯЕМ КРАСИВОЕ ОТОБРАЖЕНИЕ (НЕ ЛОМАЕТ ЛОГИКУ)
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

    # ✅ ОПТИМИЗИРОВАННЫЙ QUERYSET (СУЩЕСТВУЮЩАЯ ЛОГИКА + PREFETCH)
    def get_queryset(self, request):
        return File.objects.all().select_related(
            'owner'
        ).prefetch_related('tags')

    # ✅ СУЩЕСТВУЮЩИЙ МЕТОД (НЕ ТРОГАЕМ)
    def save_model(self, request, obj, form, change):
        obj.owner = obj.owner or request.user
        obj.save()
    
    # ========================================================================
    # НОВЫЕ МЕТОДЫ ДЛЯ ОТОБРАЖЕНИЯ (НЕ ЛОМАЮТ СУЩЕСТВУЮЩУЮ ЛОГИКУ)
    # ========================================================================
    
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
            tags_html.append(format_html('<span>...+{}</span>', obj.tags.count() - 5))
        return format_html(' '.join(tags_html))
    
    @admin.display(description='Ссылка')
    def file_url(self, obj):
        if obj.url:
            return format_html(
                '<a href="{}" target="_blank">🔗 Открыть</a>',
                obj.url
            )
        return '—'
    
    # ========================================================================
    # НОВЫЕ ГРУППОВЫЕ ДЕЙСТВИЯ
    # ========================================================================
    
    @admin.action(description='Активировать выбранные файлы')
    def activate_files(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'✅ Активировано {updated} файлов.')
    
    @admin.action(description='Деактивировать выбранные файлы')
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
        
        context = {
            'title': 'Добавить тег',
            'form': form,
            'queryset': queryset,
            'action': 'add_tag_to_files',
        }
        return self.render_changeform(request, context)
    
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
        
        context = {
            'title': 'Удалить тег',
            'form': form,
            'queryset': queryset,
            'action': 'remove_tag_from_files',
        }
        return self.render_changeform(request, context)


# ====================================================================================
# PlaylistAdmin - ПОЛНАЯ ОПТИМИЗАЦИЯ (сохраняем существующую логику)
# ====================================================================================

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    """Плейлисты."""

    # ✅ СУЩЕСТВУЮЩИЕ ПОЛЯ + НОВЫЕ
    list_display = (
        'id',
        'name',
        'owner',
        'files_count',        # НОВОЕ (удобно)
        'files_preview',       # НОВОЕ (предпросмотр)
        'playlist_type_icon',  # НОВОЕ (тип плейлиста)
        'created'
    )
    
    # ✅ СУЩЕСТВУЮЩИЕ НАСТРОЙКИ
    search_fields = ('name',)
    raw_id_fields = ('owner', 'files')
    show_full_result_count = False
    
    # ✅ НОВЫЕ НАСТРОЙКИ
    list_per_page = 50
    filter_horizontal = ('files',)
    actions = ['clear_playlist', 'duplicate_playlist']
    
    readonly_fields = ('id', 'created')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'owner', 'id')
        }),
        ('Файлы плейлиста', {
            'fields': ('files', 'playlist_composition'),
        }),
        ('Системная информация', {
            'fields': ('created',),
            'classes': ('collapse',)
        }),
    )

    # ✅ ОПТИМИЗИРОВАННЫЙ QUERYSET
    def get_queryset(self, request):
        return Playlist.objects.all().select_related(
            'owner'
        ).prefetch_related('files', 'files__tags').annotate(
            _files_count=Count('files')
        )
    
    # ========================================================================
    # НОВЫЕ МЕТОДЫ ДЛЯ ОТОБРАЖЕНИЯ
    # ========================================================================
    
    @admin.display(description='Файлов')
    def files_count(self, obj):
        count = getattr(obj, '_files_count', obj.files.count())
        if count == 0:
            return '📁 0'
        return f'📁 {count}'
    
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
                    '<a href="{}" title="{}" style="text-decoration: none; margin-right: 8px;">{} {}</a>',
                    file_url, file.name, type_icon, name
                )
            )
        
        if obj.files.count() > 5:
            preview_html.append(format_html('<span>...+{}</span>', obj.files.count() - 5))
        
        return format_html(' '.join(preview_html))
    
    @admin.display(description='Тип')
    def playlist_type_icon(self, obj):
        first_file = obj.files.first()
        if not first_file:
            return '❓ Пустой'
        
        type_info = {
            0: ('🎵 Музыкальный', '#4CAF50'),
            1: ('🎬 Видео', '#2196F3'),
            2: ('🖼️ Изображения', '#FF9800'),
            3: ('📜 Бегущая строка', '#9C27B0'),
            4: ('📢 Рекламный', '#F44336'),
        }
        type_name, color = type_info.get(first_file.type, ('❓ Смешанный', '#999'))
        
        types = set(obj.files.values_list('type', flat=True).distinct())
        if len(types) > 1:
            return format_html('<span style="color: #FF9800;">⚠️ Смешанный</span>')
        
        return format_html('<span style="color: {};">{}</span>', color, type_name)
    
    def playlist_composition(self, obj):
        """Состав плейлиста"""
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
        
        composition_html = ['<div style="display: flex; gap: 15px; flex-wrap: wrap;">']
        for type_id, count in composition.items():
            if count > 0:
                type_name, color = type_names.get(type_id, ('❓ Другое', '#999'))
                composition_html.append(
                    format_html(
                        '<div style="background: {}10; padding: 5px 10px; border-radius: 8px; border-left: 3px solid {};">'
                        '<strong>{}</strong> <span style="color: #666;">{} шт</span></div>',
                        color, color, type_name, count
                    )
                )
        composition_html.append('</div>')
        
        return format_html(''.join(composition_html))
    
    # ========================================================================
    # НОВЫЕ ГРУППОВЫЕ ДЕЙСТВИЯ
    # ========================================================================
    
    @admin.action(description='🗑️ Очистить выбранные плейлисты')
    def clear_playlist(self, request, queryset):
        count = 0
        for playlist in queryset:
            files_count = playlist.files.count()
            playlist.files.clear()
            count += files_count
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


# ====================================================================================
# TagAdmin - ОПТИМИЗИРОВАННЫЙ (сохраняем существующую логику)
# ====================================================================================

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Тематика."""

    # ✅ СУЩЕСТВУЮЩИЕ ПОЛЯ + НОВОЕ
    list_display = ('id', 'name', 'color', 'files_count')
    show_full_result_count = False
    
    # ✅ НОВЫЙ МЕТОД
    @admin.display(description='Файлов')
    def files_count(self, obj):
        return obj.files.count()
    
    # ✅ ОПТИМИЗИРОВАННЫЙ QUERYSET
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            files_count=Count('files')
        )



# from django.contrib import admin

# from .models import File, Playlist, Tag


# @admin.register(File)
# class FileAdmin(admin.ModelAdmin):
#     """Файл."""

#     @admin.display(description='Продолжительность')
#     def full_length(self, obj):
#         try:
#             return f'{obj.length:%H:%M:%S}'
#         except TypeError:
#             return obj.length

#     @admin.display(description='Размер')
#     def formatted_size(self, obj):
#         if obj.size // 1024 >= 1:
#             formatted_tail = obj.size % 1048576 // 1000
#             return f'{obj.size // 1048576}.{formatted_tail}Mb'
#         else:
#             return f'{obj.size // 1024}Kb'

#     list_display = (
#         'id',
#         'name',
#         'owner',
#         'full_length',
#         'formatted_size',
#         'is_active',
#         'created'
#     )
#     search_fields = ('name',)
#     raw_id_fields = ('owner', 'tags')
#     show_full_result_count = False

#     def get_queryset(self, request):
#         return File.objects.all().select_related(
#             'owner'
#         )

#     def save_model(self, request, obj, form, change):
#         obj.owner = obj.owner or request.user
#         obj.save()


# @admin.register(Playlist)
# class PlaylistAdmin(admin.ModelAdmin):
#     """Плейлисты."""

#     list_display = (
#         'id',
#         'name',
#         'owner'
#     )
#     search_fields = ('name',)
#     raw_id_fields = ('owner', 'files')
#     show_full_result_count = False

#     def get_queryset(self, request):
#         return Playlist.objects.all().select_related(
#             'owner'
#         ).prefetch_related('files')


# @admin.register(Tag)
# class TagAdmin(admin.ModelAdmin):
#     """Тематика."""

#     list_display = ('id', 'name', 'color')
#     show_full_result_count = False
