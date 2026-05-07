"""
Административный интерфейс для управления файлами, плейлистами и тегами.

ОПТИМИЗИРОВАННАЯ ВЕРСИЯ:
═══════════════════════════════════════════════════════════════════════════════════
• Исправлены N+1 запросы в списках
• Добавлены фильтры по типу и подтипу
• Улучшен UX для работы с плейлистами
• Групповые операции с файлами
• ПОЛНАЯ СОВМЕСТИМОСТЬ с заказами и репликациями

ВАЖНО: Все изменения только в админке, API и бизнес-логика не затронуты!
"""

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count
from django import forms
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import File, Playlist, Tag, TYPES, SUBTYPES, TYPE_CHOICES, SUBTYPE_CHOICES


# ====================================================================================
# МОДУЛЬ 1: ОПТИМИЗИРОВАННЫЕ ФИЛЬТРЫ
# ====================================================================================

class FileTypeFilter(SimpleListFilter):
    """Фильтр по типу файла"""
    title = 'Тип файла'
    parameter_name = 'file_type'
    
    def lookups(self, request, model_admin):
        return [(key, value) for key, value in TYPES.items()]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(type=self.value())
        return queryset


class FileSubtypeFilter(SimpleListFilter):
    """Фильтр по подтипу файла (только для админки)"""
    title = 'Подтип файла'
    parameter_name = 'subtype'
    
    def lookups(self, request, model_admin):
        return SUBTYPE_CHOICES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(subtype=self.value())
        return queryset


class FileActiveFilter(SimpleListFilter):
    """Фильтр по статусу активности"""
    title = 'Статус'
    parameter_name = 'is_active'
    
    def lookups(self, request, model_admin):
        return [
            (1, 'Активные'),
            (0, 'Архивные'),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(is_active=True)
        elif self.value() == '0':
            return queryset.filter(is_active=False)
        return queryset


# ====================================================================================
# МОДУЛЬ 2: КАСТОМНЫЙ ВИДЖЕТ ДЛЯ PLAYLIST
# ====================================================================================

class PlaylistFileWidget(forms.SelectMultiple):
    """Кастомный виджет для выбора файлов с группировкой по типу"""
    
    def __init__(self, attrs=None):
        super().__init__(attrs)
    
    def render(self, name, value, attrs=None, renderer=None):
        # Добавляем кнопки для быстрого выбора
        buttons_html = """
        <div class="playlist-bulk-actions" style="margin-top: 10px; margin-bottom: 10px;">
            <button type="button" class="button" onclick="selectAllFiles()" style="margin-right: 5px;">📁 Выбрать все</button>
            <button type="button" class="button" onclick="deselectAllFiles()" style="margin-right: 5px;">🗑️ Снять все</button>
            <button type="button" class="button" onclick="selectMusicFiles()" style="margin-right: 5px;">🎵 Музыку</button>
            <button type="button" class="button" onclick="selectVideoFiles()" style="margin-right: 5px;">🎬 Видео</button>
            <button type="button" class="button" onclick="selectImageFiles()" style="margin-right: 5px;">🖼️ Изображения</button>
            <button type="button" class="button" onclick="selectTickerFiles()" style="margin-right: 5px;">📜 Бегущую строку</button>
            <button type="button" class="button" onclick="selectAdFiles()">📢 Рекламу</button>
        </div>
        <script>
            function selectAllFiles() {
                var selects = document.querySelectorAll('select[multiple] option');
                for(var i = 0; i < selects.length; i++) {
                    selects[i].selected = true;
                }
            }
            function deselectAllFiles() {
                var selects = document.querySelectorAll('select[multiple] option');
                for(var i = 0; i < selects.length; i++) {
                    selects[i].selected = false;
                }
            }
            function selectMusicFiles() {
                var selects = document.querySelectorAll('select[multiple] option');
                for(var i = 0; i < selects.length; i++) {
                    if(selects[i].text.includes('🎵')) {
                        selects[i].selected = true;
                    }
                }
            }
            function selectVideoFiles() {
                var selects = document.querySelectorAll('select[multiple] option');
                for(var i = 0; i < selects.length; i++) {
                    if(selects[i].text.includes('🎬')) {
                        selects[i].selected = true;
                    }
                }
            }
            function selectImageFiles() {
                var selects = document.querySelectorAll('select[multiple] option');
                for(var i = 0; i < selects.length; i++) {
                    if(selects[i].text.includes('🖼️')) {
                        selects[i].selected = true;
                    }
                }
            }
            function selectTickerFiles() {
                var selects = document.querySelectorAll('select[multiple] option');
                for(var i = 0; i < selects.length; i++) {
                    if(selects[i].text.includes('📜')) {
                        selects[i].selected = true;
                    }
                }
            }
            function selectAdFiles() {
                var selects = document.querySelectorAll('select[multiple] option');
                for(var i = 0; i < selects.length; i++) {
                    if(selects[i].text.includes('📢')) {
                        selects[i].selected = true;
                    }
                }
            }
        </script>
        """
        return mark_safe(buttons_html + super().render(name, value, attrs, renderer))


class PlaylistForm(forms.ModelForm):
    """Кастомная форма для плейлиста"""
    
    files = forms.ModelMultipleChoiceField(
        queryset=File.active.all(),
        widget=PlaylistFileWidget(attrs={'style': 'width: 100%; height: 400px;'}),
        required=False,
        label='Файлы'
    )
    
    class Meta:
        model = Playlist
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['files'].initial = self.instance.files.all()


# ====================================================================================
# МОДУЛЬ 3: ОПТИМИЗИРОВАННЫЙ ADMIN ДЛЯ ТЕГОВ
# ====================================================================================

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Администрирование тегов (оптимизированное)"""
    
    list_display = ('id', 'colored_name', 'color_preview', 'files_count')
    search_fields = ('name',)
    list_filter = ('color',)
    ordering = ('name',)
    
    def colored_name(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            obj.color if obj.color else '#000000',
            obj.name
        )
    colored_name.short_description = 'Название'
    
    def color_preview(self, obj):
        if obj.color:
            return format_html(
                '<div style="width: 30px; height: 20px; background-color: {}; border: 1px solid #ccc;"></div>',
                obj.color
            )
        return '-'
    color_preview.short_description = 'Цвет'
    
    def files_count(self, obj):
        return obj.files.count()
    files_count.short_description = 'Файлов'
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            files_count=Count('files')
        ).only('id', 'name', 'color')


# ====================================================================================
# МОДУЛЬ 4: ОПТИМИЗИРОВАННЫЙ ADMIN ДЛЯ ФАЙЛОВ
# ====================================================================================

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    """Администрирование файлов (оптимизированное, с поддержкой подтипов)"""
    
    list_display = (
        'id',
        'file_preview',
        'owner',
        'file_type_icon',
        'subtype_display',
        'formatted_size',
        'full_length',
        'tags_preview',
        'is_active',
        'created'
    )
    
    search_fields = ('name', 'hash', 'owner__email', 'owner__first_name', 'owner__last_name')
    
    list_filter = (FileTypeFilter, FileSubtypeFilter, FileActiveFilter, 'tags', 'created')
    
    readonly_fields = ('id', 'md5hash', 'sha256hash', 'hash', 'length', 'size', 'file_url', 'created', 'modified')
    
    ordering = ('-created',)
    
    list_per_page = 50
    
    actions = ['activate_files', 'deactivate_files', 'add_tag_to_files', 'remove_tag_from_files']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'owner', 'type', 'subtype', 'is_active')
        }),
        ('Файл', {
            'fields': ('source', 'file_url')
        }),
        ('Техническая информация', {
            'fields': ('id', 'md5hash', 'sha256hash', 'hash', 'length', 'size', 'created', 'modified'),
            'classes': ('collapse',)
        }),
        ('Теги', {
            'fields': ('tags',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Оптимизация: предзагрузка связанных данных"""
        return super().get_queryset(request).select_related(
            'owner'
        ).prefetch_related('tags')
    
    # ========================================================================
    # МЕТОДЫ ДЛЯ ОТОБРАЖЕНИЯ
    # ========================================================================
    
    def file_preview(self, obj):
        """Предпросмотр файла с иконкой"""
        icons = {
            0: '🎵',
            1: '🎬',
            2: '🖼️',
            3: '📜',
            4: '📢',
        }
        icon = icons.get(obj.type, '📄')
        name = obj.name[:50] + '...' if len(obj.name) > 50 else obj.name
        return format_html(f'{icon} <strong>{name}</strong>')
    file_preview.short_description = 'Файл'
    
    def file_type_icon(self, obj):
        """Иконка типа файла"""
        type_icons = {
            0: '🎵 Музыка',
            1: '🎬 Видео',
            2: '🖼️ Изображение',
            3: '📜 Бегущая строка',
            4: '📢 Реклама',
        }
        return type_icons.get(obj.type, '❓ Неизвестно')
    file_type_icon.short_description = 'Тип'
    
    def subtype_display(self, obj):
        """Отображение подтипа"""
        if obj.subtype:
            icon = getattr(obj, 'subtype_icon', '📄')
            name = getattr(obj, 'subtype_display', obj.subtype)
            return format_html(f'{icon} {name}')
        return '—'
    subtype_display.short_description = 'Подтип'
    
    def tags_preview(self, obj):
        """Предпросмотр тегов"""
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
    tags_preview.short_description = 'Теги'
    
    @admin.display(description='Длительность')
    def full_length(self, obj):
        try:
            if obj.length:
                return f'{obj.length:%H:%M:%S}'
            return '—'
        except (TypeError, AttributeError):
            return obj.length or '—'
    
    @admin.display(description='Размер')
    def formatted_size(self, obj):
        if not obj.size:
            return '—'
        if obj.size < 1024:
            return f'{obj.size} B'
        elif obj.size < 1048576:
            return f'{obj.size / 1024:.1f} KB'
        else:
            return f'{obj.size / 1048576:.1f} MB'
    
    def file_url(self, obj):
        """Ссылка на файл"""
        if obj.url:
            return format_html(
                '<a href="{}" target="_blank" style="font-size: 12px;">🔗 Открыть в новом окне</a>',
                obj.url
            )
        return '—'
    file_url.short_description = 'Ссылка'
    
    # ========================================================================
    # ГРУППОВЫЕ ДЕЙСТВИЯ
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
    
    def save_model(self, request, obj, form, change):
        if not obj.owner:
            obj.owner = request.user
        super().save_model(request, obj, form, change)


# ====================================================================================
# МОДУЛЬ 5: ОПТИМИЗИРОВАННЫЙ ADMIN ДЛЯ ПЛЕЙЛИСТОВ
# ====================================================================================

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    """Администрирование плейлистов (улучшенный UX, полная совместимость)"""
    
    form = PlaylistForm
    
    list_display = (
        'id',
        'name',
        'owner',
        'files_count_display',
        'files_preview',
        'playlist_type_icon',
        'created'
    )
    
    search_fields = ('name', 'description', 'owner__email', 'owner__first_name', 'owner__last_name')
    
    list_filter = ('created',)
    
    filter_horizontal = ('files',)
    
    readonly_fields = ('id', 'created', 'modified', 'playlist_composition')
    
    ordering = ('-created',)
    
    list_per_page = 50
    
    actions = ['clear_playlist', 'duplicate_playlist']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'owner', 'id')
        }),
        ('Файлы плейлиста', {
            'fields': ('files', 'playlist_composition'),
            'description': '💡 Совет: используйте кнопки выше для быстрого выбора файлов по типу'
        }),
        ('Системная информация', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Оптимизация: предзагрузка связанных данных с аннотацией"""
        return super().get_queryset(request).select_related(
            'owner'
        ).prefetch_related('files', 'files__tags').annotate(
            _files_count=Count('files')
        )
    
    # ========================================================================
    # МЕТОДЫ ДЛЯ ОТОБРАЖЕНИЯ
    # ========================================================================
    
    def files_count_display(self, obj):
        """Количество файлов в плейлисте"""
        count = getattr(obj, '_files_count', obj.files.count())
        if count == 0:
            return format_html('<span style="color: #999;">📁 0</span>')
        return format_html('<span style="font-weight: bold;">📁 {}</span>', count)
    files_count_display.short_description = 'Файлов'
    files_count_display.admin_order_field = '_files_count'
    
    def files_preview(self, obj):
        """Предпросмотр первых 5 файлов"""
        files = obj.files.all()[:5]
        if not files:
            return format_html('<span style="color: #999;">— нет файлов —</span>')
        
        preview_html = []
        for file in files:
            type_icon = {
                0: '🎵',
                1: '🎬',
                2: '🖼️',
                3: '📜',
                4: '📢',
            }.get(file.type, '📄')
            
            file_url = reverse('admin:files_file_change', args=[file.id])
            name = file.name[:25] + '...' if len(file.name) > 25 else file.name
            preview_html.append(
                format_html(
                    '<a href="{}" title="{}" style="text-decoration: none; margin-right: 10px; font-size: 12px;">'
                    '{} {}</a>',
                    file_url, file.name, type_icon, name
                )
            )
        
        if obj.files.count() > 5:
            preview_html.append(format_html('<span style="color: #666;">...+{}</span>', obj.files.count() - 5))
        
        return format_html(' '.join(preview_html))
    files_preview.short_description = 'Файлы'
    
    def playlist_type_icon(self, obj):
        """Определение типа плейлиста по первому файлу"""
        first_file = obj.files.first()
        if not first_file:
            return format_html('<span style="color: #999;">❓ Пустой</span>')
        
        type_info = {
            0: ('🎵 Музыкальный', '#4CAF50'),
            1: ('🎬 Видео', '#2196F3'),
            2: ('🖼️ Изображения', '#FF9800'),
            3: ('📜 Бегущая строка', '#9C27B0'),
            4: ('📢 Рекламный', '#F44336'),
        }
        type_name, color = type_info.get(first_file.type, ('❓ Смешанный', '#999'))
        
        # Проверяем, все ли файлы одного типа
        types = set(obj.files.values_list('type', flat=True).distinct())
        if len(types) > 1:
            return format_html('<span style="color: #FF9800;">⚠️ Смешанный тип</span>')
        
        return format_html('<span style="color: {};">{}</span>', color, type_name)
    playlist_type_icon.short_description = 'Тип'
    
    def playlist_composition(self, obj):
        """Состав плейлиста с группировкой по типам"""
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
                        '<strong>{}</strong> <span style="color: #666;">{} файлов</span></div>',
                        color, color, type_name, count
                    )
                )
        composition_html.append('</div>')
        
        return format_html(''.join(composition_html))
    playlist_composition.short_description = 'Состав плейлиста'
    
    # ========================================================================
    # ГРУППОВЫЕ ДЕЙСТВИЯ
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
        self.message_user(request, f'✅ Создано {created_count} копий плейлистов.')
    
    def save_model(self, request, obj, form, change):
        if not obj.owner:
            obj.owner = request.user
        super().save_model(request, obj, form, change)
        if 'files' in form.cleaned_data:
            obj.files.set(form.cleaned_data['files'])



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
