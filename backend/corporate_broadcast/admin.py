from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from .models import BroadcastDemo, BroadcastDemoAsset


class DemoAssetFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        materials = [form for form in self.forms if form.cleaned_data and not form.cleaned_data.get("DELETE")]
        if self.instance.is_published and not any(form.cleaned_data.get("role") != "poster" and form.instance.is_playable for form in materials):
            raise ValidationError("Для публикации добавьте хотя бы один активный аудио-, видео- или графический материал. Постер сам по себе не является демо.")


class DemoAssetInline(admin.TabularInline):
    model = BroadcastDemoAsset
    formset = DemoAssetFormSet
    autocomplete_fields = ("file",)
    extra = 1


@admin.register(BroadcastDemo)
class BroadcastDemoAdmin(admin.ModelAdmin):
    list_display = ("title", "format", "is_published", "sort_order", "modified")
    list_filter = ("format", "is_published")
    search_fields = ("title", "description")
    readonly_fields = ("id", "created", "modified")
    inlines = (DemoAssetInline,)
