"""Audio artwork can be assigned in the parent playlist editor."""

from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AutocompleteSelectMultiple
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.forms.models import BaseInlineFormSet

from files.models import File, Playlist, PlaylistItem, PlaylistItemVisual
from files.playlist_content import is_audio_file
from files.playlist_admin_service import (
    playlist_graph_signature,
    resolved_graph_signature,
    validate_playlist_graph_change,
)


class PlaylistItemInlineForm(forms.ModelForm):
    images = forms.ModelMultipleChoiceField(
        queryset=File.objects.none(), required=False, label="Картинки к этому аудио",
        help_text="Найдите картинки по названию. Одна показывается весь аудиоролик, несколько — по очереди. Время рассчитывает плеер. Только для рекламного аудио.",
        widget=AutocompleteSelectMultiple(PlaylistItemVisual._meta.get_field("file"), admin.site),
    )

    class Meta:
        model = PlaylistItem
        fields = ("position", "file", "images")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._existing_visuals = list(self.instance.visuals.all()) if self.instance.pk else []
        self._existing_ids = {row.file_id for row in self._existing_visuals}
        self.fields["images"].queryset = File.objects.filter(
            Q(type=2, is_active=True) | Q(pk__in=self._existing_ids)
        )
        self.initial["images"] = list(self._existing_ids)

    def clean(self):
        data = super().clean()
        selected = data.get("images")
        primary = data.get("file")
        if selected is None or primary is None:
            return data
        selected_ids = {file.pk for file in selected}
        if selected_ids and (selected_ids != self._existing_ids or primary.pk != self.instance.file_id):
            if not is_audio_file(primary):
                self.add_error("images", "Картинки сопровождения можно прикрепить только к аудиофайлу.")
        for file in selected:
            if file.pk not in self._existing_ids and (file.type != 2 or not file.is_active):
                self.add_error("images", "Выберите активные файлы-картинки.")
        return data

    @transaction.atomic
    def save_images(self):
        """Keep retained rows/order, append new choices; never delete media files."""
        selected = self.cleaned_data["images"]
        selected_ids = {file.pk for file in selected}
        PlaylistItem.objects.select_for_update().get(pk=self.instance.pk)
        current = list(self.instance.visuals.select_for_update().order_by("position", "id"))
        current_ids = {row.file_id for row in current}
        if selected_ids == current_ids:
            return
        self.instance.visuals.exclude(file_id__in=selected_ids).delete()
        # Browser submits the selected options in selection order. Retained
        # images keep their original relative order, including repeated images.
        posted = self.data.getlist(self.add_prefix("images")) if hasattr(self.data, "getlist") else self.data.get(self.add_prefix("images"), [])
        selected_by_id = {str(file.pk): file for file in selected}
        new_ids = list(dict.fromkeys(str(value) for value in posted if str(value) in selected_by_id))
        new_ids.extend(str(file.pk) for file in selected if str(file.pk) not in new_ids)
        position = max((row.position for row in current), default=-1) + 1
        for identity in new_ids:
            file = selected_by_id[identity]
            if file.pk not in current_ids:
                PlaylistItemVisual.objects.create(playlist_item=self.instance, file=file, position=position)
                position += 1
        getattr(self.instance, "_prefetched_objects_cache", {}).pop("visuals", None)

    def ordered_images(self) -> list[File]:
        """Return selected images while retaining existing duplicate rows."""

        selected = list(self.cleaned_data.get("images") or ())
        selected_by_id = {file.pk: file for file in selected}
        selected_ids = set(selected_by_id)
        ordered = [
            row.file
            for row in self._existing_visuals
            if row.file_id in selected_ids
        ]
        existing_ids = {row.file_id for row in self._existing_visuals}
        field_name = self.add_prefix("images")
        posted = (
            self.data.getlist(field_name)
            if hasattr(self.data, "getlist")
            else self.data.get(field_name, [])
        )
        if isinstance(posted, str):
            posted = [posted]
        posted_ids = [str(value) for value in posted]
        for value in posted_ids:
            match = next(
                (file for key, file in selected_by_id.items() if str(key) == value),
                None,
            )
            if match is not None and match.pk not in existing_ids:
                ordered.append(match)
                existing_ids.add(match.pk)
        for file in selected:
            if file.pk not in existing_ids:
                ordered.append(file)
                existing_ids.add(file.pk)
        return ordered


def resolved_formset_items(formset: BaseInlineFormSet):
    """Build the final ordered graph from a validated playlist inline."""

    rows = []
    for index, form in enumerate(formset.forms):
        data = getattr(form, "cleaned_data", {})
        if not data or data.get("DELETE") or data.get("file") is None:
            continue
        rows.append(
            (
                data.get("position", 0),
                index,
                {
                    "file": data["file"],
                    "images": form.ordered_images(),
                    "position": data.get("position", 0),
                },
            )
        )
    rows.sort(key=lambda row: (row[0], row[1]))
    return [row[2] for row in rows]


class PlaylistItemInlineFormSet(BaseInlineFormSet):
    """Validate the complete parent graph before admin starts writing it."""

    def clean(self):
        super().clean()
        if any(self.errors) or not self.instance.pk:
            return
        desired = resolved_formset_items(self)
        if not self.instance.items.exists() and not desired:
            return
        if playlist_graph_signature(self.instance) == resolved_graph_signature(desired):
            return
        try:
            validate_playlist_graph_change(
                self.instance,
                will_be_empty=not desired,
            )
        except ValidationError as exc:
            raise ValidationError(exc.messages) from exc


class PlaylistItemAdminForm(forms.ModelForm):
    """Validate standalone item moves before the admin starts writing."""

    class Meta:
        model = PlaylistItem
        fields = "__all__"

    def clean(self):
        data = super().clean()
        target = data.get("playlist")
        file = data.get("file")
        position = data.get("position")
        if target is None or file is None or position is None:
            return data

        original = None
        if self.instance.pk:
            original = PlaylistItem.objects.select_related("playlist").get(
                pk=self.instance.pk
            )
        affected: dict[object, bool] = {}
        if original is None:
            affected[target.pk] = False
        elif original.playlist_id != target.pk:
            affected[original.playlist_id] = (
                PlaylistItem.objects.filter(playlist_id=original.playlist_id).count()
                == 1
            )
            affected[target.pk] = False
        else:
            rows = list(
                PlaylistItem.objects.filter(playlist=target)
                .order_by("position", "pk")
                .values_list("pk", "file_id", "position")
            )
            before = [file_id for _, file_id, _ in rows]
            after = [
                (position if pk == original.pk else old_position, pk, file.pk if pk == original.pk else file_id)
                for pk, file_id, old_position in rows
            ]
            after_ids = [file_id for _, _, file_id in sorted(after)]
            if before != after_ids:
                affected[target.pk] = False

        for playlist_id, will_be_empty in affected.items():
            try:
                validate_playlist_graph_change(
                    Playlist.objects.get(pk=playlist_id),
                    will_be_empty=will_be_empty,
                )
            except ValidationError as exc:
                self.add_error(None, exc)
        return data


class PlaylistItemVisualInlineFormSet(BaseInlineFormSet):
    """Reject semantic gallery changes before saving a legacy-bound item."""

    def clean(self):
        super().clean()
        if any(self.errors) or not self.instance.pk:
            return
        current = list(
            self.instance.visuals.order_by("position", "pk").values_list(
                "file_id", flat=True
            )
        )
        desired = []
        for index, form in enumerate(self.forms):
            data = getattr(form, "cleaned_data", {})
            if not data or data.get("DELETE") or data.get("file") is None:
                continue
            desired.append((data.get("position", 0), index, data["file"].pk))
        desired_ids = [file_id for _, _, file_id in sorted(desired)]
        if current == desired_ids:
            return
        try:
            validate_playlist_graph_change(self.instance.playlist)
        except ValidationError as exc:
            raise ValidationError(exc.messages) from exc
