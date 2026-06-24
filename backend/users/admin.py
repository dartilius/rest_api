"""
Административный интерфейс для модели CustomUser.

ОПТИМИЗАЦИЯ:
───────────────────────────────────────────────────────────────────────────────
1. get_queryset() с select_related и prefetch_related
2. only() для выборки только необходимых полей
3. Кеширование на 5 минут
"""

from django.contrib import admin
from django.core.cache import cache
from django.db.models import Prefetch

from users.models import CustomUser, ContactInfo


class ContactInfoInline(admin.TabularInline):
    """Контактная информация пользователя (inline)."""

    model = ContactInfo
    extra = 0
    min_num = 0
    can_delete = True

    verbose_name = "Контакт"
    verbose_name_plural = "Контактная информация"

    fields = (
        "type",
        "meaning",
        "vidtel",
        "vidmail",
        "ext",
        "basic",
        "comment",
    )


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """Пользователь."""

    inlines = (ContactInfoInline,)

    list_display = (
        'id',
        'full_name_display',
        'role',
        'email',
        'phone_number',
        'is_active',
        'created',
    )

    search_fields = (
        'id',
        'last_name',
        'first_name',
        'middle_name',
        'email',
        'phone_number',
    )

    list_filter = (
        'role',
        'is_active',
    )

    ordering = ('-created',)
    show_full_result_count = False
    readonly_fields = ('created',)
    list_per_page = 50

    # =========================================================================
    # ОПТИМИЗИРОВАННЫЙ QUERYSET
    # =========================================================================

    def get_queryset(self, request):
        """
        Оптимизированный запрос с предзагрузкой связей.

        Использует:
        - select_related для FK связей
        - prefetch_related для M2M связей
        - only() для выборки только необходимых полей
        - Кеширование на 5 минут
        """
        cache_key = f"user_admin_qs_{request.user.id}"
        queryset = cache.get(cache_key)

        if queryset is None:
            queryset = (
                CustomUser.objects
                .select_related()  # FK связей нет
                .prefetch_related(
                    Prefetch(
                        'contacts_cp',
                        queryset=ContactInfo.objects.only(
                            'id', 'user_id', 'type', 'meaning',
                            'vidtel', 'vidmail', 'basic', 'comment', 'ext'
                        )
                    )
                )
                .only(
                    'id', 'last_name', 'first_name', 'middle_name',
                    'role', 'email', 'phone_number', 'is_active',
                    'created', 'code1c',
                )
            )
            cache.set(cache_key, queryset, 300)

        return queryset

    @admin.display(description='ФИО')
    def full_name_display(self, obj):
        return obj.full_name

    # =========================================================================
    # ДЕЙСТВИЯ
    # =========================================================================

    actions = ['clear_cache']

    def clear_cache(self, request, queryset):
        """Очищает кеш пользователей."""
        cache.delete_pattern("user_admin_qs_*")
        self.message_user(request, 'Кэш очищен')

    clear_cache.short_description = "Очистить кэш"


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    """Администрирование контактной информации."""

    list_display = ("id", "type", "meaning")
    show_full_result_count = False
    raw_id_fields = ("user",)

    def get_queryset(self, request):
        return ContactInfo.objects.select_related("user").only(
            'id', 'type', 'meaning', 'user_id',
            'vidtel', 'vidmail', 'basic', 'comment', 'ext'
        )

# # from django.contrib import admin

# # from users.models import CustomUser


# # @admin.register(CustomUser)
# # class CustomUserAdmin(admin.ModelAdmin):
# #     """Пользователь."""

# #     list_display = (
# #         'id',
# #         'full_name_display',
# #         'role',
# #         'email',
# #         'phone_number',
# #         'is_active',
# #         'created',
# #     )
# #     search_fields = (
# #         'id',
# #         'last_name',
# #         'first_name',
# #         'middle_name',
# #         'role',
# #         'is_active',
# #     )
# #     show_full_result_count = False

# #     @admin.display(description='ФИО')
# #     def full_name_display(self, obj):
# #         return obj.full_name
# from django.contrib import admin

# from users.models import CustomUser, ContactInfo


# class ContactInfoInline(admin.TabularInline):
#     """Контактная информация пользователя (inline)."""

#     model = ContactInfo
#     extra = 0
#     min_num = 0
#     can_delete = True

#     verbose_name = "Контакт"
#     verbose_name_plural = "Контактная информация"

#     fields = (
#         "type",
#         "meaning",
#         "vidtel",
#         "vidmail",
#         "ext",
#         "basic",
#         "comment",
#     )


# @admin.register(CustomUser)
# class CustomUserAdmin(admin.ModelAdmin):
#     """Пользователь."""

#     inlines = (ContactInfoInline,)

#     list_display = (
#         'id',
#         'full_name_display',
#         'role',
#         'email',
#         'phone_number',
#         'is_active',
#         'created',
#     )

#     search_fields = (
#         'id',
#         'last_name',
#         'first_name',
#         'middle_name',
#         'email',
#         'phone_number',
#     )

#     list_filter = (
#         'role',
#         'is_active',
#     )

#     ordering = ('-created',)
#     show_full_result_count = False

#     readonly_fields = ('created',)

#     @admin.display(description='ФИО')
#     def full_name_display(self, obj):
#         return obj.full_name


# @admin.register(ContactInfo)
# class ContactInfoAdmin(admin.ModelAdmin):
#     """Администрирование контактной информации."""

#     list_display = ("id", "type", "meaning")
#     show_full_result_count = False
#     raw_id_fields = ("user",)

#     def get_queryset(self, request):
#         return ContactInfo.objects.select_related("user")