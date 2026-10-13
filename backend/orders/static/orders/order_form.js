"use strict";
(function () {
    const descriptions = {
        workday: "Реклама идёт равномерно с открытия до закрытия точки. Укажите число выходов заказа в час; ролики плейлиста выбираются по очереди.",
        hourly_slots: "Реклама идёт равномерно в рабочее время точки. Ролики плейлиста выбираются по очереди.",
        open_offset: "Показы начинаются через указанное время после открытия точки и идут до закрытия.",
        close_offset: "Показы идут с открытия и заканчиваются за указанное время до закрытия точки.",
        fixed_time: "Реклама идёт каждый день в указанном интервале, независимо от времени открытия точки.",
        open_to_fixed: "Показы идут с открытия точки до указанного времени.",
        fixed_to_close: "Показы идут с указанного времени до закрытия точки.",
        start_to_close: "Первый выход — в указанное время. Затем реклама повторяется равномерно до закрытия точки.",
        continuous: "Реклама заменяет визуальный фон на всё рабочее время. Частота не задаётся. Если реклама без звука, фоновая музыка продолжает играть.",
        event: "Это существующий заказ по событию. Настройка этого режима пока недоступна; его сохранённые параметры остаются прежними."
    };
    function viewFor(placement, policy, permanent) {
        const ad = placement === "advertising";
        return {
            ad, frequency: ad && !["continuous", "event"].includes(policy),
            start: ad && ["fixed_time", "fixed_to_close", "start_to_close"].includes(policy),
            end: ad && ["fixed_time", "open_to_fixed"].includes(policy),
            offset: ad && ["open_offset", "close_offset"].includes(policy),
            audio: ad && policy !== "event", permanent: placement === "background",
            endDate: !(placement === "background" && permanent),
            automaticAudio: ad && policy === "continuous",
            description: ad ? (descriptions[policy] || "Выберите, когда должна выходить реклама.")
                : "Фон воспроизводится по рабочему времени точки. Видео играется полностью, картинка — заданное число секунд. Музыка идёт отдельно."
        };
    }
    if (typeof module !== "undefined" && module.exports) module.exports = {viewFor};
    if (typeof document === "undefined") return;
    function mount() {
        const guide = document.getElementById("order-form-guide");
        if (!guide) return;
        const field = name => document.getElementById("id_" + name);
        const row = name => document.querySelector(".form-row.field-" + name);
        const placement = () => field("placement") ? field("placement").value : guide.dataset.placement;
        const policy = () => field("playback_policy") ? field("playback_policy").value : guide.dataset.policy;
        function show(name, visible) {
            const container = row(name);
            if (!container) return;
            container.hidden = !visible;
            container.querySelectorAll("input, select, textarea").forEach(input => {
                // Django itself disables the legacy event selector.
                if (name === "playback_policy" && guide.dataset.policy === "event") return;
                input.disabled = !visible;
            });
        }
        function render() {
            const state = viewFor(placement(), policy(), field("is_permanent") ? field("is_permanent").checked : guide.dataset.permanent === "true");
            if (placement() === "background" && field("playback_policy")) field("playback_policy").value = "workday";
            show("playback_policy", state.ad);
            show("times_in_hour", state.frequency);
            show("offset_minutes", state.offset);
            show("offset_seconds", state.offset);
            show("start_time", state.start);
            show("end_time", state.end);
            show("advertising_audio", state.audio);
            show("suppress_background_audio", state.audio);
            show("suppress_background_visual", state.audio);
            show("is_permanent", state.permanent);
            show("ends_at", state.endDate);
            [["times_in_hour", state.frequency], ["start_time", state.start], ["end_time", state.end], ["offset_minutes", state.offset]].forEach(([name, required]) => {
                if (field(name)) field(name).required = required;
            });
            ["starts_at", "ends_at"].forEach(name => {
                const container = row(name);
                if (container) container.querySelectorAll("input").forEach(input => {
                    input.required = state.ad || (name === "ends_at" && state.endDate);
                });
            });
            const schedule = document.querySelector("fieldset.order-ad-schedule");
            const audio = document.querySelector("fieldset.order-ad-options");
            if (schedule) schedule.hidden = !state.ad;
            if (audio) audio.hidden = !state.audio;
            if (state.automaticAudio) {
                if (field("suppress_background_audio")) field("suppress_background_audio").checked = field("advertising_audio").value !== "muted";
                if (field("suppress_background_visual")) field("suppress_background_visual").checked = true;
            }
            ["suppress_background_audio", "suppress_background_visual"].forEach(name => {
                if (field(name)) field(name).disabled = !state.audio || state.automaticAudio;
            });
            document.getElementById("order-policy-help").textContent = state.description;
        }
        ["placement", "playback_policy", "is_permanent"].forEach(name => {
            if (field(name)) field(name).addEventListener("change", render);
        });
        if (field("advertising_audio")) field("advertising_audio").addEventListener("change", () => {
            if (field("suppress_background_audio")) field("suppress_background_audio").checked = field("advertising_audio").value !== "muted";
            if (field("suppress_background_visual")) field("suppress_background_visual").checked = true;
            render();
        });
        render();
    }
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
    else mount();
})();
