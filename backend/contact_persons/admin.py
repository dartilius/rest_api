from django.contrib import admin
from .models import Contact, ContactInformation
from django.core.exceptions import ValidationError


class ContactInformationInline(admin.StackedInline):
    model = ContactInformation
    extra = 1
    min_num = 0
    max_num = 10  # можно изменить по необходимости
    fields = ("basic", "type", "vidtel", "vidmail", "meaning", "ext", "comment")
    verbose_name = "Контактная информация"
    verbose_name_plural = "Контактная информация"
    show_change_link = True

    def save_new(self, form, commit=True):
        # валидация через clean()
        instance = form.save(commit=False)
        try:
            instance.clean()
        except ValidationError as e:
            form.add_error(None, e)
        if commit:
            instance.save()
        return instance


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("surname", "name", "vid", "is_active")
    search_fields = ("surname", "name")
    inlines = [ContactInformationInline]

    def save_model(self, request, obj, form, change):
        """Обеспечиваем сохранение с валидностью и обновление inline."""
        obj.save()
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return Contact.objects.select_related("nomenclatures")

@admin.register(ContactInformation)
class ContactInformationAdmin(admin.ModelAdmin):
    list_display = ("type", "meaning", "contact", "basic", "is_active")
    list_filter = ("type", "basic")
    search_fields = ("meaning", "contact__surname", "contact__name")
