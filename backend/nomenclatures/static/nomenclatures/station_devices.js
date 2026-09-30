(function ($) {
    "use strict";
    $(function () {
        const station = $("#id_nomenclature");
        const endpoint = station.attr("data-station-devices-url");
        if (!endpoint) return;
        let pending;
        function setChoices(selector, choices) {
            const field = $(selector).empty();
            choices.forEach(function (choice) {
                field.append(new Option(choice[1], choice[0]));
            });
            field.trigger("change");
        }
        station.on("change", function () {
            if (pending) pending.abort();
            const empty = [["", "Сначала выберите точку вещания"]];
            setChoices("#id_audio_device_id", empty);
            setChoices("#id_display_id", empty);
            if (!station.val()) return;
            pending = $.getJSON(endpoint, {station: station.val()})
                .done(function (data) {
                    setChoices("#id_audio_device_id", data.audio);
                    setChoices("#id_display_id", data.displays);
                })
                .fail(function (_, status) {
                    if (status === "abort") return;
                    const failed = [["", "Не удалось загрузить устройства. Выберите точку повторно."]];
                    setChoices("#id_audio_device_id", failed);
                    setChoices("#id_display_id", failed);
                });
        });
    });
})(django.jQuery);
