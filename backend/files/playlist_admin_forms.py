"""Формы основных файлов плейлиста в админке."""

from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from files.models import PlaylistItem
from files.playlist_admin_service import (
    HISTORICAL_VISUALS_ERROR,
    playlist_graph_signature,
    resolved_graph_signature,
    validate_historical_playlist_items,
    validate_playlist_graph_change,
)


class PlaylistItemInlineForm(forms.ModelForm):
    """Редактируем основной файл, сохраняя его место в очереди."""

    class Meta:
        model = PlaylistItem
        fields = ("file",)

    def clean(self):
        data = super().clean()
        primary = data.get("file")
        if (
            self.instance.pk
            and primary is not None
            and primary.pk != self.instance.file_id
            and self.instance.visuals.exists()
        ):
            self.add_error("file", HISTORICAL_VISUALS_ERROR)
        return data


def resolved_formset_items(formset: BaseInlineFormSet):
    """Собираем итоговый порядок файлов из проверенных строк формы."""

    rows = []
    for index, form in enumerate(formset.forms):
        data = getattr(form, "cleaned_data", {})
        if not data or data.get("DELETE") or data.get("file") is None:
            continue
        rows.append(
            (
                form.instance.position if form.instance.pk else index,
                index,
                {
                    "item_id": form.instance.pk,
                    "file": data["file"],
                    "position": form.instance.position if form.instance.pk else index,
                },
            )
        )
    rows.sort(key=lambda row: (row[0], row[1]))
    return [row[2] for row in rows]


class PlaylistItemInlineFormSet(BaseInlineFormSet):
    """Проверяем весь состав перед записью в базу."""

    def clean(self):
        super().clean()
        if any(self.errors) or not self.instance.pk:
            return
        desired = resolved_formset_items(self)
        if not self.instance.items.exists() and not desired:
            return
        try:
            validate_historical_playlist_items(self.instance, desired)
        except ValidationError as exc:
            raise ValidationError(exc.messages) from exc
        if playlist_graph_signature(self.instance) == resolved_graph_signature(desired):
            return
        try:
            validate_playlist_graph_change(
                self.instance,
                desired_items=desired,
                will_be_empty=not desired,
            )
        except ValidationError as exc:
            raise ValidationError(exc.messages) from exc
