(function ($) {
    "use strict";
    $(function () {
        const field = $("#id_interval_volume_rows");
        const editor = $("[data-station-interval-editor]");
        const container = editor.find("#station-interval-rows");
        if (!field.length || !container.length) return;
        const days = [
            ["all", "Все дни недели"], ["mon", "Понедельник"], ["tue", "Вторник"],
            ["wed", "Среда"], ["thu", "Четверг"], ["fri", "Пятница"],
            ["sat", "Суббота"], ["sun", "Воскресенье"]
        ];
        const channels = [
            ["background_left", "Фон — левый, %"], ["background_right", "Фон — правый, %"],
            ["advertisement_left", "Реклама — левый, %"], ["advertisement_right", "Реклама — правый, %"]
        ];
        let rows = [];
        let sequence = 0;
        let enabled = true;
        let malformed = false;
        let edited = false;
        try {
            const parsed = JSON.parse(field.val() || "[]");
            if (!Array.isArray(parsed)) throw new Error("invalid rows");
            rows = parsed;
        } catch (_) { malformed = true; }

        function sync() { field.val(JSON.stringify(rows)); }

        function updateEnabled() {
            container.find("input, select").prop("disabled", !enabled);
            editor.find("button").prop("disabled", !enabled);
        }

        function control(card, row, key, title, type, extraClass) {
            const id = "station-interval-" + sequence + "-" + key;
            const box = $("<div>").addClass(extraClass || "");
            $("<label>").attr("for", id).text(title).appendTo(box);
            let input;
            if (type === "select") {
                input = $("<select>");
                days.forEach(function (day) { input.append(new Option(day[1], day[0])); });
            } else {
                input = $("<input>").attr("type", type);
                if (type === "time") input.attr("step", "1");
                else input.attr({min: "0", max: "100", step: "1", inputmode: "numeric"});
            }
            input.attr({id: id, "data-interval-field": key}).val(row[key] == null ? "" : row[key]);
            input.on("input change", function () {
                row[key] = type === "number" && input.val() !== "" ? Number(input.val()) : input.val();
                edited = true;
                malformed = false;
                sync();
            });
            input.appendTo(box);
            box.appendTo(card);
        }

        function render() {
            container.empty();
            rows.forEach(function (row, index) {
                sequence += 1;
                const card = $("<div>").addClass("station-interval-card");
                card.toggleClass("station-interval-deleted", !!row.deleted);
                const header = $("<div>").addClass("station-interval-header").appendTo(card);
                $("<h3>").text("Интервал " + (index + 1) + (row.deleted ? " — будет удалён" : "")).appendTo(header);
                $("<button>").attr("type", "button").addClass("button station-interval-remove")
                    .text(row.deleted ? "Отменить удаление" : "Удалить интервал")
                    .on("click", function () {
                        if (row.original_day && row.original_interval) row.deleted = !row.deleted;
                        else rows.splice(index, 1);
                        edited = true;
                        sync(); render();
                    }).appendTo(header);
                const grid = $("<div>").addClass("station-interval-grid").appendTo(card);
                control(grid, row, "day", "Применить к дням", "select", "station-interval-days");
                control(grid, row, "start", "С", "time");
                control(grid, row, "end", "До", "time");
                channels.forEach(function (channel) { control(grid, row, channel[0], channel[1], "number"); });
                card.appendTo(container);
            });
            editor.find(".station-interval-status").text(malformed
                ? "Не удалось прочитать интервалы. Выберите точку повторно перед отправкой."
                : rows.length ? "Изменения и удаление вступят в силу после отправки команды и подтверждения плеером."
                    : "Интервалов нет. В течение дня используется обычная громкость.");
            updateEnabled();
        }

        editor.find(".station-interval-add").on("click", function () {
            rows.push({day: "all", start: "", end: "", background_left: "", background_right: "", advertisement_left: "", advertisement_right: ""});
            edited = true;
            malformed = false; sync(); render();
            container.find(".station-interval-card").last().find("select").trigger("focus");
        });
        field.closest("form").on("submit", function (event) {
            if (!enabled) return;
            if (malformed) { event.preventDefault(); window.alert("Выберите точку повторно: интервалы не удалось прочитать."); }
            else sync();
        });
        window.RMCStationIntervals = {
            load: function (customVolumes, preserve) {
                if (preserve || edited) return;
                rows = [];
                days.slice(1).forEach(function (day) {
                    Object.entries(customVolumes[day[0]] || {}).forEach(function (entry) {
                        const times = entry[0].split("-");
                        rows.push(Object.assign({}, entry[1], {
                            day: day[0], start: times[0], end: times[1],
                            original_day: day[0], original_interval: entry[0]
                        }));
                    });
                });
                malformed = false; sync(); render();
            },
            reset: function () { rows = []; malformed = false; edited = false; sync(); render(); },
            setEnabled: function (value) { enabled = value; updateEnabled(); }
        };
        render();
    });
})(django.jQuery);
