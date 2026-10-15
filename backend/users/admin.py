"""Django admin configuration for the custom user model."""

from django.contrib import admin

from users.models import CustomUser, ContactInfo
from users.models import PersonalDataConsent, PrivacyRequest, PrivacyErasure
from users.privacy_services import resolve_privacy_request


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


class PrivacyStaffAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return (request.user.has_perm('users.manage_privacy')
                and super().has_module_permission(request))

    def has_view_permission(self, request, obj=None):
        return (request.user.has_perm('users.manage_privacy')
                and super().has_view_permission(request, obj))

    def has_change_permission(self, request, obj=None):
        return (request.user.has_perm('users.manage_privacy')
                and super().has_change_permission(request, obj))

    def has_add_permission(self, request):
        return (request.user.has_perm('users.manage_privacy')
                and super().has_add_permission(request))

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PersonalDataConsent)
class PersonalDataConsentAdmin(PrivacyStaffAdmin):
    list_display = ('id', 'purpose', 'document_version', 'accepted_at', 'revoked_at')
    list_filter = ('purpose', 'document_version')
    readonly_fields = tuple(field.name for field in PersonalDataConsent._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PrivacyErasure)
class PrivacyErasureAdmin(PrivacyStaffAdmin):
    readonly_fields = tuple(field.name for field in PrivacyErasure._meta.fields)
    list_display = ('subject_type', 'subject_id', 'erased_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PrivacyRequest)
class PrivacyRequestAdmin(PrivacyStaffAdmin):
    list_display = ('id', 'kind', 'received_at', 'status', 'completed_at')
    readonly_fields = ('handled_by', 'completed_at', 'delete_after')
    raw_id_fields = ('user', 'feedback', 'consent')

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.completed_at:
            return tuple(field.name for field in self.model._meta.fields)
        return self.readonly_fields

    def has_change_permission(self, request, obj=None):
        if obj and obj.completed_at:
            return False
        return super().has_change_permission(request, obj)

    def save_model(self, request, obj, form, change):
        resolve_privacy_request(obj, request.user)


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
        """Return only the fields used by the changelist."""
        return super().get_queryset(request).only(
            'id', 'last_name', 'first_name', 'middle_name',
            'role', 'email', 'phone_number', 'is_active', 'created',
        )

    @admin.display(description='ФИО')
    def full_name_display(self, obj):
        return obj.full_name

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
