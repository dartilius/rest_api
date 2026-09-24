"""A focused, permission-aware section for 1C-managed entities in Django admin."""

from types import MethodType

from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path, reverse


ONE_C_ADMIN_MODELS = {
    ("addresses", "Address"),
    ("brands", "Brand"),
    ("counterparties", "Counterparty"),
    ("nomenclatures", "Nomenclature"),
    ("nomenclatures", "TypeOfPlace"),
    ("nomenclatures", "NomenclatureTenant"),
    ("nomenclatures", "DiscountRule"),
    ("nomenclatures", "NomenclatureMedia"),
}


def _one_c_models(app_list):
    return [
        model
        for app in app_list
        for model in app["models"]
        if (app["app_label"], model["object_name"]) in ONE_C_ADMIN_MODELS
    ]


def _one_c_section(models):
    return {
        "name": "1С",
        "app_label": "one_c",
        "app_url": reverse("admin:one_c_index"),
        "has_module_perms": True,
        "models": models,
    }


def configure_one_c_admin_section():
    if getattr(admin.site, "_one_c_section_configured", False):
        return

    original_get_app_list = admin.site.get_app_list
    original_get_urls = admin.site.get_urls

    def one_c_index(request):
        models = _one_c_models(original_get_app_list(request))
        context = {
            **admin.site.each_context(request),
            "title": "1С",
            "app_label": "one_c",
            "app_list": [_one_c_section(models)] if models else [],
        }
        return TemplateResponse(request, "admin/app_index.html", context)

    def get_app_list(self, request, app_label=None):
        app_list = original_get_app_list(request, app_label)
        if app_label is not None:
            return app_list

        models = _one_c_models(app_list)
        return [*app_list, _one_c_section(models)] if models else app_list

    def get_urls(self):
        return [
            path("1c/", self.admin_view(one_c_index), name="one_c_index"),
            *original_get_urls(),
        ]

    admin.site.get_app_list = MethodType(get_app_list, admin.site)
    admin.site.get_urls = MethodType(get_urls, admin.site)
    admin.site._one_c_section_configured = True


configure_one_c_admin_section()
