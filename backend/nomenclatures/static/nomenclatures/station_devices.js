(function ($) {
    "use strict";
    $(function () {
        const station = $("#id_nomenclature");
        const commandForm = station.closest("form");
        const endpoint = station.attr("data-station-devices-url");
        const day = $("#id_day");
        const settingGroup = $("#id_setting_group");
        const volumeFields = {
            background_left: $("#id_background_left_volume"),
            background_right: $("#id_background_right_volume"),
            advertisement_left: $("#id_advertisement_left_volume"),
            advertisement_right: $("#id_advertisement_right_volume")
        };
        const settingSections = [
            "volume",
            "background",
            "worktime",
            "audio_device",
            "display",
            "visual_output"
        ];
        if (!endpoint) return;
        let pending;
        let defaultVolumes = {};
        let requestGeneration = 0;

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
                    setDefaultVolumes();
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
            return field.data("confirmed-value") === undefined || value !== field.data("confirmed-value");
        }

        function updateVisibleSection() {
            const selected = settingGroup.val();
            settingSections.forEach(function (name) {
                $(".station-command-" + name).toggle(name === selected);
            });
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
        commandForm.on("submit", function (event) {
            if (settingGroup.val() !== "volume") return;

            const fieldsToSubmit = Object.keys(volumeFields).filter(function (key) {
                return valueNeedsSubmission(key);
            });
            if (fieldsToSubmit.length === 0) {
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
            loadStation(station.val(), true);
        }
    });
})(django.jQuery);
