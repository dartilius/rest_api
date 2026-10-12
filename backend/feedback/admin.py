from django.contrib import admin
from feedback.models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("created", "request_type", "name", "company", "phone", "email")
    list_filter = ("request_type", "consent", "created")
    search_fields = ("name", "company", "phone", "email")
    readonly_fields = tuple(field.name for field in Feedback._meta.fields)
    date_hierarchy = "created"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
