from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from brands.models import Brand

from .models import BroadcastDemo, BroadcastDemoAsset, TypesOfPlaceBroadcast, TypeOfFormats, BroadcastLanding


class BroadcastAdminStyle:
    change_form_template = "admin/corporate_broadcast/change_form.html"

    class Media:
        css = {"all": ("corporate_broadcast/admin.css",)}
        js = ("corporate_broadcast/admin.js",)


class RelatedContentAdmin(BroadcastAdminStyle, admin.ModelAdmin):
    """Keep helpers available in popups with their normal permissions."""

    def get_model_perms(self, request):
        return {}  # One entry point in navigation: BroadcastLanding.


class DemoAssetFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        materials = [form for form in self.forms if form.cleaned_data and not form.cleaned_data.get("DELETE")]
        if self.instance.is_published and not any(form.cleaned_data.get("role") != "poster" and form.instance.is_playable for form in materials):
            raise ValidationError("Для публикации добавьте хотя бы один активный аудио-, видео- или графический материал. Постер сам по себе не является демо.")


class DemoAssetInline(admin.StackedInline):
    model = BroadcastDemoAsset
    formset = DemoAssetFormSet
    autocomplete_fields = ("file",)
    fields = (("role", "sort_order"), "file", "caption")
    extra = 1
    verbose_name_plural = "Материалы демо: аудио, видео, изображения"


@admin.register(BroadcastDemo)
class BroadcastDemoAdmin(RelatedContentAdmin):
    list_display = ("title", "format", "is_published", "sort_order", "modified")
    list_filter = ("format", "is_published")
    search_fields = ("title", "description")
    readonly_fields = ("id", "created", "modified")
    fieldsets = (
        ("Демо для посетителей", {
            "fields": ("title", "format", "description", "transcript"),
            "description": "Добавьте материалы ниже. Новый файл можно загрузить кнопкой «Добавить» рядом с выбором файла.",
        }),
        ("Публикация", {
            "fields": ("is_published", "sort_order"),
            "description": "На сайте отображается только опубликованное демо с активными материалами.",
        }),
        ("Служебная информация", {
            "fields": ("id", "created", "modified"), "classes": ("collapse",),
        }),
    )
    inlines = (DemoAssetInline,)

@admin.register(TypesOfPlaceBroadcast)
class TypesOfPlaceBroadcastAdmin(RelatedContentAdmin):
    list_display = ("title", "type_of_place", "format_type", "is_active")
    list_filter = ("type_of_place", "format_type", "is_active")
    search_fields = ("title", "description", "type_of_place__name")
    fieldsets = (("Формат для блока", {
        "fields": ("title", "type_of_place", "format_type", "description", "is_active"),
        "description": "Название и описание будут показаны в блоке. Изменение общего формата затронет все блоки, где он выбран.",
    }),)

    def save_model(self, request, obj, form, change):
        obj.name = obj.title
        if not obj.owner_id:
            obj.owner = request.user
        super().save_model(request, obj, form, change)



@admin.register(TypeOfFormats)
class TypeOfFormatsAdmin(RelatedContentAdmin):
    list_display = ("format_type", "description")
    list_filter = ("format_type",)
    search_fields = ("name", "description")
    fields = ("format_type", "description", "demo", "is_active")

    def save_model(self, request, obj, form, change):
        obj.name = obj.get_format_type_display()
        if not obj.owner_id:
            obj.owner = request.user
        super().save_model(request, obj, form, change)


class BroadcastLandingForm(forms.ModelForm):
    class Meta:
        model = BroadcastLanding
        fields = ("title", "description", "logo_brands", "format_type", "demo")
        widgets = {
            "title": forms.TextInput(attrs={"class": "vTextField", "placeholder": "Например: Вещание для торговых сетей"}),
            "description": forms.Textarea(attrs={"rows": 5}),
        }
        help_texts = {
            "title": "Заголовок отдельного блока на странице корпоративного вещания.",
            "description": "Описание под заголовком. Переносы строк сохраняются; HTML не требуется.",
            "logo_brands": "Выберите бренды или добавьте новый. Логотип берётся из карточки бренда.",
            "format_type": "Кнопки рядом позволяют создать или изменить формат в отдельном окне.",
            "demo": "Выберите демо или создайте новое с материалами. Для показа на сайте отметьте его как опубликованное.",
        }


@admin.register(BroadcastLanding)
class BroadcastLandingAdmin(BroadcastAdminStyle, admin.ModelAdmin):
    form = BroadcastLandingForm
    change_list_template = "admin/corporate_broadcast/change_list.html"
    list_display = ("title", "format_title", "brands_count", "demo_status")
    list_filter = ("format_type__format_type", "demo__is_published")
    search_fields = ("title", "description", "format_type__title", "demo__title")
    list_per_page = 25
    save_on_top = True
    filter_horizontal = ("logo_brands",)
    autocomplete_fields = ("format_type", "demo")
    readonly_fields = ("content_preview",)
    fieldsets = (
        ("1. Заголовок и описание", {"fields": ("title", "description")}),
        ("2. Логотипы брендов", {"fields": ("logo_brands",)}),
        ("3. Формат и демо", {
            "fields": ("format_type", "demo"),
            "description": "Кнопка «Добавить» создаёт связанную запись, «Изменить» открывает выбранную без ухода с этой формы. Общие демо и форматы могут использоваться в нескольких блоках.",
        }),
        ("4. Проверка перед сохранением", {"fields": ("content_preview",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("format_type", "demo").prefetch_related(
            "logo_brands"
        ).annotate(selected_brands_count=Count("logo_brands", distinct=True))

    @admin.display(description="Формат")
    def format_title(self, obj):
        return obj.format_type.title if obj.format_type else "Не выбран"

    @admin.display(description="Бренды", ordering="selected_brands_count")
    def brands_count(self, obj):
        return obj.selected_brands_count

    @admin.display(description="Демо")
    def demo_status(self, obj):
        if not obj.demo:
            return "Не выбрано"
        return format_html(
            '<span class="cb-badge {}">{}</span>',
            "cb-badge-success" if obj.demo.is_published else "cb-badge-warning",
            "Опубликовано" if obj.demo.is_published else "Черновик — скрыт на сайте",
        )

    @admin.display(description="Сохранённый блок")
    def content_preview(self, obj):
        if not obj or not obj.pk:
            return "Предпросмотр появится после первого сохранения блока."
        return format_html(
            '<div class="cb-preview"><span>Блок на сайте</span><h3>{}</h3><p>{}</p></div>',
            obj.title, obj.description or "Описание не заполнено",
        )

    def render_change_form(self, request, context, *args, **kwargs):
        obj = context.get("original")
        brands = []
        brand_admin = self.admin_site.get_model_admin(Brand)
        if obj:
            for brand in obj.logo_brands.all():
                brands.append({
                    "name": brand.name,
                    "has_logo": bool(brand.logotype),
                    "deleted": brand.is_deleted,
                    "logo_url": reverse("broadcast-landing-brand-logo", kwargs={"pk": obj.pk, "brand_id": brand.pk}) if brand.logotype and not brand.is_deleted else None,
                    "edit_url": reverse(f"{self.admin_site.name}:brands_brand_change", args=[brand.pk]) + "?_popup=1" if brand_admin.has_change_permission(request, brand) else None,
                })
        context["cb_selected_brands"] = brands
        return super().render_change_form(request, context, *args, **kwargs)
