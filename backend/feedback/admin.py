from django.contrib import admin
from feedback.models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("created", "request_type", "name", "status", "contract_status", "delete_after")
    list_filter = ("request_type", "status", "contract_status", "consent", "created")
    search_fields = ("name", "company", "phone", "email")
    readonly_fields = tuple(field.name for field in Feedback._meta.fields if field.name not in {
        'status', 'closed_at', 'contract_status', 'contract_reference',
        'lawful_retention_until', 'lawful_retention_basis',
    })
    date_hierarchy = "created"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return (request.user.has_perm('users.manage_privacy')
                and super().has_change_permission(request, obj))

    def has_view_permission(self, request, obj=None):
        return (request.user.has_perm('users.manage_privacy')
                and super().has_view_permission(request, obj))

    def has_delete_permission(self, request, obj=None):
        return False
