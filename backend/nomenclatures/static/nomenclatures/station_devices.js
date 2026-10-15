(function ($) {
    "use strict";
    $(function () {
        const station = $("#id_nomenclature");
        const commandForm = station.closest("form");
        const endpoint = station.attr("data-station-devices-url");
        const day = $("#id_volume_day").length ? $("#id_volume_day") : $("#id_day");
        const settingGroup = $("#id_setting_group");
        const settingGroups = commandForm.find("input[name='setting_groups']");
        const intervalsField = $("#id_interval_volume_rows");
        const volumeFields = {
            background_left: $("#id_background_left_volume"),
            background_right: $("#id_background_right_volume"),
            advertisement_left: $("#id_advertisement_left_volume"),
            advertisement_right: $("#id_advertisement_right_volume")
        };
        const settingSections = [
            "volume",
            "interval_volume",
            "background",
            "worktime",
            "audio_device",
            "display",
            "visual_output"
        ];
        const dayTargetFields = {
            volume: "#id_volume_all_days",
            background: "#id_background_all_days",
            worktime: "#id_worktime_all_days"
        };
        if (!endpoint) return;
        let pending;
        let defaultVolumes = {};
        let requestGeneration = 0;

        function selectedGroups() {
            return settingGroups.length
                ? settingGroups.filter(":checked").map(function () { return this.value; }).get()
                : [settingGroup.val()];
        }

        function intervals() { return window.RMCStationIntervals; }

        function setChoices(selector, choices) {
            const field = $(selector).empty();
            choices.forEach(function (choice) {
                field.append(new Option(choice[1], choice[0]));
            });
            field.trigger("change");
        }

        function resetVolumeFields() {
            defaultVolumes = {};
            Object.keys(volumeFields).forEach(function (key) {
                volumeFields[key]
                    .prop("disabled", false)
                    .val("")
                    .removeData("confirmed-value")
                    .removeData("volume-dirty");
            });
        }

        function setDefaultVolumes() {
            const values = defaultVolumes[day.val()];
            Object.keys(volumeFields).forEach(function (key) {
                const field = volumeFields[key];
                const hasValue = values && Object.prototype.hasOwnProperty.call(values, key);
                const value = hasValue ? values[key] : "";
                field.prop("disabled", false);
                if (hasValue) {
                    field.data("confirmed-value", String(value));
                } else {
                    field.removeData("confirmed-value");
                }
                if (!field.data("volume-dirty")) {
                    field.val(value);
                }
            });
        }

        function loadStation(stationId, preserveFormValues) {
            requestGeneration += 1;
            const generation = requestGeneration;
            if (pending) pending.abort();

            if (!preserveFormValues) {
                const empty = [["", "Сначала выберите точку вещания"]];
                setChoices("#id_audio_device_id", empty);
                setChoices("#id_display_id", empty);
                resetVolumeFields();
                $("#id_settings_revision").val("");
                if (intervals()) intervals().reset();
            }
            if (!stationId) return;

            pending = $.getJSON(endpoint, {station: stationId})
                .done(function (data) {
                    if (generation !== requestGeneration || station.val() !== stationId) return;
                    if (!preserveFormValues) {
                        setChoices("#id_audio_device_id", data.audio);
                        setChoices("#id_display_id", data.displays);
                    }
                    defaultVolumes = data.default_volumes || {};
                    if (!preserveFormValues) $("#id_settings_revision").val(data.settings_revision);
                    setDefaultVolumes();
                    if (intervals()) intervals().load(data.custom_volumes || {}, preserveFormValues);
                    updateVisibleSection();
                })
                .fail(function (_, status) {
                    if (status === "abort" || generation !== requestGeneration || station.val() !== stationId) return;
                    if (preserveFormValues) return;
                    const failed = [["", "Не удалось загрузить устройства. Выберите точку повторно."]];
                    setChoices("#id_audio_device_id", failed);
                    setChoices("#id_display_id", failed);
                });
        }

        function valueNeedsSubmission(key) {
            const field = volumeFields[key];
            const value = String(field.val());
            if (value === "") return false;
            if ($("#id_volume_all_days").prop("checked")) {
                if (!field.data("volume-dirty")) return false;
                return ["mon", "tue", "wed", "thu", "fri", "sat", "sun"].some(function (name) {
                    return !defaultVolumes[name] || String(defaultVolumes[name][key]) !== value;
                });
            }
            return field.data("confirmed-value") === undefined || value !== field.data("confirmed-value");
        }

        function updateVisibleSection() {
            const selected = selectedGroups();
            settingSections.forEach(function (name) {
                const section = $(".station-command-" + name);
                const active = selected.includes(name);
                section.toggle(active);
                if (settingGroups.length) {
                    section.find("input:not([type='hidden']), select, textarea, button").prop("disabled", !active);
                }
            });
            if (intervals()) intervals().setEnabled(selected.includes("interval_volume"));
            if (settingGroups.length) return;
            const dayRow = day.closest(".form-row");
            const targetField = dayTargetFields[selected[0]];
            const allDaysRow = targetField ? $(targetField).closest(".form-row") : $();
            if (!dayRow.length) return;
            if (!allDaysRow.length) {
                dayRow.hide();
                return;
            }
            dayRow.insertBefore(allDaysRow).show();
        }

        Object.keys(volumeFields).forEach(function (key) {
            const field = volumeFields[key];
            if (field.val() !== "") {
                field.data("volume-dirty", true);
            }
            field.on("input change", function () {
                field.data("volume-dirty", true);
            });
        });
        station.on("change", function () {
            loadStation(station.val(), false);
        });
        day.on("change", setDefaultVolumes);
        settingGroup.on("change", updateVisibleSection);
        settingGroups.on("change", updateVisibleSection);
        commandForm.on("submit", function (event) {
            if (!selectedGroups().includes("volume")) return;

            const fieldsToSubmit = Object.keys(volumeFields).filter(function (key) {
                return valueNeedsSubmission(key);
            });
            if (fieldsToSubmit.length === 0 && selectedGroups().length === 1) {
                event.preventDefault();
                window.alert("Измените хотя бы один канал громкости перед применением настройки.");
                return;
            }
            Object.keys(volumeFields).forEach(function (key) {
                if (!fieldsToSubmit.includes(key)) {
                    volumeFields[key].prop("disabled", true);
                }
            });
        });
        updateVisibleSection();
        if (station.val()) {
            const preserve = intervalsField.length
                ? intervalsField.attr("data-bound") === "true"
                : true;
            loadStation(station.val(), preserve);
        }
    });
})(django.jQuery);
