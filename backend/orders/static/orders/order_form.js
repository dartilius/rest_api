"use strict";
(function () {
    const descriptions = {
        workday: "Реклама идёт равномерно с открытия до закрытия точки. Укажите число выходов заказа в час; ролики плейлиста выбираются по очереди.",
        hourly_slots: "Реклама идёт равномерно в рабочее время точки. Ролики плейлиста выбираются по очереди.",
        open_offset: "Показы начинаются через указанное время после открытия точки и идут до закрытия.",
        close_offset: "Показы идут с открытия и заканчиваются за указанное время до закрытия точки.",
        fixed_time: "В выбранные дни реклама идёт в указанном интервале, независимо от времени открытия точки.",
        open_to_fixed: "Показы идут с открытия точки до указанного времени.",
        fixed_to_close: "Показы идут с указанного времени до закрытия точки.",
        start_to_close: "Первый выход — в указанное время. Затем реклама повторяется равномерно до закрытия точки.",
        continuous: "В выбранные дни реклама заменяет визуальный фон на всё рабочее время. Частота не задаётся. Если реклама без звука, фоновая музыка продолжает играть.",
        event: "Это существующий заказ по событию. Настройка этого режима пока недоступна; его сохранённые параметры остаются прежними."
    };
    function viewFor(placement, policy, permanent) {
        const ad = placement === "advertising";
        const timed = placement === "background" || (ad && policy !== "event");
        return {
            ad, frequency: ad && !["continuous", "event"].includes(policy),
            start: ad && ["fixed_time", "fixed_to_close", "start_to_close"].includes(policy),
            end: ad && ["fixed_time", "open_to_fixed"].includes(policy),
            offset: ad && ["open_offset", "close_offset"].includes(policy),
            audio: ad && policy !== "event", permanent: placement === "background",
            endDate: !(placement === "background" && permanent),
            weekdays: timed && !permanent,
            automaticAudio: ad && policy === "continuous",
            description: ad ? (descriptions[policy] || "Выберите, когда должна выходить реклама.")
                : "Фон воспроизводится по рабочему времени точки. Видео играется полностью, картинка — заданное число секунд. Музыка идёт отдельно."
        };
    }
    function moveChosen(options, direction) {
        const ordered = Array.from(options);
        if (direction === "up") {
            for (let index = 1; index < ordered.length; index++) {
                if (ordered[index].selected && !ordered[index - 1].selected) {
                    [ordered[index - 1], ordered[index]] = [ordered[index], ordered[index - 1]];
                }
            }
        } else if (direction === "down") {
            for (let index = ordered.length - 2; index >= 0; index--) {
                if (ordered[index].selected && !ordered[index + 1].selected) {
                    [ordered[index], ordered[index + 1]] = [ordered[index + 1], ordered[index]];
                }
            }
        }
        return ordered;
    }
    if (typeof module !== "undefined" && module.exports) module.exports = {viewFor, moveChosen};
    if (typeof document === "undefined") return;

    function selectedAudioImages(root) {
        const selected = new Map();
        root.querySelectorAll("select[data-audio-id]").forEach(select => {
            selected.set(select.dataset.audioId, Array.from(select.options, option => ({
                id: option.value, name: option.textContent
            })));
        });
        return selected;
    }
    function optionFor(image) {
        const option = document.createElement("option");
        option.value = image.id;
        option.textContent = image.name;
        return option;
    }
    function refreshAvailable(group) {
        const available = group.querySelector("[data-images-available]");
        const chosen = group.querySelector("[data-images-chosen]");
        const query = group.querySelector("[data-image-search]").value.trim().toLocaleLowerCase();
        const selected = new Set(Array.from(available.selectedOptions, option => option.value));
        const used = new Set(Array.from(chosen.options, option => option.value));
        available.replaceChildren();
        group.imageChoices.forEach(image => {
            if (used.has(image.id) || !image.name.toLocaleLowerCase().includes(query)) return;
            const option = optionFor(image);
            option.selected = selected.has(image.id);
            available.appendChild(option);
        });
    }
    function bindImageGroup(group) {
        const available = group.querySelector("[data-images-available]");
        const chosen = group.querySelector("[data-images-chosen]");
        group.imageChoices = Array.from(available.options, option => ({id: option.value, name: option.textContent}));
        // Сохраняем название назначенной картинки, даже если файл стал неактивным.
        Array.from(chosen.options).forEach(option => {
            if (!group.imageChoices.some(image => image.id === option.value)) {
                group.imageChoices.push({id: option.value, name: option.textContent});
            }
        });
        group.querySelector("[data-image-search]").addEventListener("input", () => refreshAvailable(group));
        group.querySelectorAll("[data-image-action]").forEach(button => {
            button.addEventListener("click", () => {
                const action = button.dataset.imageAction;
                if (action === "add") {
                    Array.from(chosen.options).forEach(option => { option.selected = false; });
                    Array.from(available.selectedOptions).forEach(option => {
                        const added = optionFor({id: option.value, name: option.textContent});
                        added.selected = true;
                        chosen.appendChild(added);
                    });
                    refreshAvailable(group);
                    chosen.focus();
                } else if (action === "remove") {
                    Array.from(chosen.selectedOptions).forEach(option => option.remove());
                    refreshAvailable(group);
                    chosen.focus();
                } else {
                    moveChosen(chosen.options, action).forEach(option => chosen.appendChild(option));
                    chosen.focus();
                }
            });
        });
        refreshAvailable(group);
    }
    function replaceAudioImageGroups(root, payload) {
        const selected = selectedAudioImages(root);
        root.querySelectorAll(".order-audio-image-group, .order-audio-images-status").forEach(node => node.remove());
        const audios = Array.isArray(payload.audios) ? payload.audios : [];
        const images = Array.isArray(payload.images) ? payload.images : [];
        if (!audios.length) {
            const status = document.createElement("p");
            status.className = "order-audio-images-status help";
            status.textContent = "В выбранном плейлисте нет аудиофайлов.";
            root.prepend(status);
            return;
        }
        audios.forEach(audio => {
            const group = document.createElement("div");
            group.className = "order-audio-image-group";
            group.dataset.audioGroup = audio.id;
            // Названия файлов вставляем только как текст, без выполнения HTML.
            group.innerHTML = '<h3></h3><div class="order-image-columns"><div class="order-image-column">' +
                '<label>Найти картинку</label><input type="search" data-image-search placeholder="Название картинки">' +
                '<label>Доступные картинки</label><select data-images-available multiple size="6"></select>' +
                '<button type="button" data-image-action="add">Добавить выбранные →</button></div>' +
                '<div class="order-image-column"><label>Порядок показа — сверху вниз</label>' +
                '<select data-images-chosen multiple size="6"></select><div class="order-image-actions">' +
                '<button type="button" data-image-action="up">↑ Выше</button>' +
                '<button type="button" data-image-action="down">↓ Ниже</button>' +
                '<button type="button" data-image-action="remove">Убрать</button></div></div></div>';
            group.querySelector("h3").textContent = audio.name;
            const search = group.querySelector("[data-image-search]");
            const available = group.querySelector("[data-images-available]");
            const chosen = group.querySelector("[data-images-chosen]");
            const baseId = "id_audio_images_" + audio.id;
            [search, available, chosen].forEach((control, index) => {
                control.id = baseId + ["_search", "_available", ""][index];
                group.querySelectorAll("label")[index].htmlFor = control.id;
            });
            chosen.name = "audio_images__" + audio.id;
            chosen.dataset.audioId = audio.id;
            images.forEach(image => available.appendChild(optionFor(image)));
            (selected.get(audio.id) || []).forEach(image => chosen.appendChild(optionFor(image)));
            root.insertBefore(group, root.querySelector(".order-audio-images-feedback"));
            bindImageGroup(group);
        });
    }
    function mount() {
        const guide = document.getElementById("order-form-guide");
        if (!guide) return;
        const field = name => document.getElementById("id_" + name);
        const row = name => document.querySelector(".form-row.field-" + name);
        const placement = () => field("placement") ? field("placement").value : guide.dataset.placement;
        const policy = () => field("playback_policy") ? field("playback_policy").value : guide.dataset.policy;
        const audioImagesRoot = document.querySelector("[data-order-audio-images]");
        const orderForm = guide.closest("form");
        let imageRequest = 0;
        let imageController = null;
        let imageLoadBlocked = false;
        const imageFeedback = text => {
            const feedback = audioImagesRoot && audioImagesRoot.querySelector(".order-audio-images-feedback");
            if (feedback) feedback.textContent = text;
            const retry = audioImagesRoot && audioImagesRoot.querySelector("[data-image-retry]");
            if (retry) retry.hidden = !imageLoadBlocked;
        };
        if (audioImagesRoot) audioImagesRoot.querySelectorAll("[data-audio-group]").forEach(bindImageGroup);
        if (orderForm && audioImagesRoot) orderForm.addEventListener("submit", event => {
            if (placement() === "advertising" && imageLoadBlocked) {
                event.preventDefault();
                imageFeedback("Список картинок не загружен. Повторите загрузку перед сохранением.");
                audioImagesRoot.querySelector("[data-image-retry]").focus();
                return;
            }
            audioImagesRoot.querySelectorAll("[data-images-chosen]").forEach(select => {
                if (!select.disabled) Array.from(select.options).forEach(option => { option.selected = true; });
            });
        });
        function show(name, visible) {
            const container = row(name);
            if (!container) return;
            container.hidden = !visible;
            container.querySelectorAll("input, select, textarea").forEach(input => {
                // Старый выбор событий отключается самой формой Django.
                if (name === "playback_policy" && guide.dataset.policy === "event") return;
                input.disabled = !visible;
            });
        }
        const weekdayInputs = () => Array.from(document.querySelectorAll('input[name="weekdays"]'));
        function syncAllDays() {
            const allDays = field("all_days");
            const days = weekdayInputs();
            if (allDays && days.length) allDays.checked = days.every(input => input.checked);
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
            show("all_days", state.weekdays);
            show("weekdays", state.weekdays);
            show("audio_images", state.ad);
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
        async function loadAudioImages() {
            const requestId = ++imageRequest;
            if (imageController) imageController.abort();
            imageController = new AbortController();
            const requestController = imageController;
            const playlistId = field("playlist").value;
            if (!playlistId) {
                replaceAudioImageGroups(audioImagesRoot, {audios: [], images: []});
                imageLoadBlocked = false;
                imageFeedback("");
                return;
            }
            imageLoadBlocked = true;
            imageFeedback("Загружаем аудио и картинки…");
            const url = new URL(audioImagesRoot.dataset.optionsUrl, window.location.origin);
            url.searchParams.set("playlist", playlistId);
            const timeout = setTimeout(() => requestController.abort(), 15000);
            try {
                const response = await fetch(url, {
                    credentials: "same-origin", headers: {Accept: "application/json"},
                    signal: requestController.signal
                });
                const payload = await response.json();
                if (requestId !== imageRequest) return;
                if (!response.ok) throw new Error(payload.error || "Не удалось загрузить файлы плейлиста.");
                replaceAudioImageGroups(audioImagesRoot, payload);
                imageLoadBlocked = false;
                imageFeedback("");
                render();
            } catch (error) {
                if (requestId !== imageRequest) return;
                imageFeedback("Не удалось загрузить список. Выбранные картинки сохранены на экране. Нажмите «Повторить загрузку».");
            } finally {
                clearTimeout(timeout);
            }
        }
        if (field("playlist") && audioImagesRoot) {
            // Autocomplete Django использует события jQuery. Обычный обработчик DOM
            // не получает программную смену выбора в Select2.
            const adminJQuery = typeof window !== "undefined" && window.django && window.django.jQuery;
            if (adminJQuery) adminJQuery(field("playlist")).on("change.orderAudioImages", loadAudioImages);
            else field("playlist").addEventListener("change", loadAudioImages);
            const retry = document.createElement("button");
            retry.type = "button";
            retry.hidden = true;
            retry.dataset.imageRetry = "1";
            retry.textContent = "Повторить загрузку";
            retry.addEventListener("click", loadAudioImages);
            audioImagesRoot.appendChild(retry);
        }
        if (field("advertising_audio")) field("advertising_audio").addEventListener("change", () => {
            if (field("suppress_background_audio")) field("suppress_background_audio").checked = field("advertising_audio").value !== "muted";
            if (field("suppress_background_visual")) field("suppress_background_visual").checked = true;
            render();
        });
        if (field("all_days")) field("all_days").addEventListener("change", () => {
            if (field("all_days").checked) weekdayInputs().forEach(input => { input.checked = true; });
        });
        weekdayInputs().forEach(input => input.addEventListener("change", syncAllDays));
        syncAllDays();
        render();
    }
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
    else mount();
})();
