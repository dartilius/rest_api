/* Native admin runtime updates. No settings, HTML from the wire, or global subscriptions. */
(function (factory) {
    const api = factory();
    if (typeof module !== "undefined" && module.exports) module.exports = api;
    if (typeof document !== "undefined") {
        const start = () => document.querySelectorAll(".js-station-runtime").forEach(node => api.mount(node));
        if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
        else start();
    }
})(function () {
    "use strict";
    function render(panel, content) {
        const doc = panel.ownerDocument;
        const result = doc.createElement("div");
        result.className = "broadcast-state";
        const text = (tag, value, parent = result) => {
            const node = doc.createElement(tag);
            node.textContent = value;
            parent.appendChild(node);
            return node;
        };
        if (!content || content.has_state !== true) {
            text("p", "Player ещё не передал состояние воспроизведения.");
        } else {
            text("p", "Режим работы: " + content.mode);
            text("p", "Сервисный режим: " + content.maintenance);
            if (content.error) text("p", "Последняя ошибка: " + content.error).className = "errornote";
            text("h4", "Реклама");
            if (content.advertisement) {
                const ad = content.advertisement;
                text("p", `${ad.name} — ${ad.type}, ${ad.status}.`);
                text("p", "Длительность: " + ad.duration);
            } else text("p", "Текущая реклама не передана.");
            text("h4", "Фоновый контент");
            if (Array.isArray(content.background) && content.background.length) {
                const wrapper = doc.createElement("div");
                wrapper.style.overflowX = "auto";
                wrapper.style.maxWidth = "100%";
                result.appendChild(wrapper);
                const table = doc.createElement("table");
                wrapper.appendChild(table);
                const head = doc.createElement("thead");
                const heading = doc.createElement("tr");
                table.appendChild(head); head.appendChild(heading);
                ["Контент", "Тип", "Состояние", "Проиграно", "Длительность"].forEach(label => {
                    text("th", label, heading).setAttribute("scope", "col");
                });
                const body = doc.createElement("tbody"); table.appendChild(body);
                content.background.forEach(item => {
                    const row = doc.createElement("tr"); body.appendChild(row);
                    [item.name, item.type, item.status, item.position, item.duration].forEach(value => text("td", value, row));
                    row.firstChild.style.overflowWrap = "anywhere";
                });
            } else text("p", "Текущий фоновый контент не передан.");
        }
        panel.replaceChildren(result);
    }

    function mount(root, dependencies = {}) {
        if (!root.dataset.pollUrl || !root.dataset.wsPath) return null;
        const win = dependencies.window || window;
        const now = dependencies.now || (() => Date.now());
        const later = dependencies.setTimeout || win.setTimeout.bind(win);
        const cancel = dependencies.clearTimeout || win.clearTimeout.bind(win);
        const get = dependencies.fetch || win.fetch.bind(win);
        const makeSocket = dependencies.makeSocket || (url => new win.WebSocket(url));
        const panel = root.querySelector("[data-runtime-content]");
        const status = root.querySelector("[data-runtime-status]");
        const updated = root.querySelector("[data-runtime-updated]");
        let ws = null, stopped = false, lastMessage = -Infinity, lastVersion = null;
        let pollTimer = null, reconnectTimer = null, pingTimer = null, controller = null;
        let backoff = 2000;
        function show(payload, channel) {
            if (stopped || !payload || payload.type !== "runtime" || !payload.content || typeof payload.content !== "object") return;
            if (!payload.version || payload.version !== lastVersion) render(panel, payload.content);
            lastVersion = payload.version;
            updated.textContent = payload.received_at ? "Последний снимок: " + payload.received_at : "Время снимка неизвестно";
            status.textContent = payload.content.has_state !== true ? "Данные о воспроизведении ещё не получены"
                : payload.stale ? "Данные устарели — показан последний полученный снимок" : channel;
        }
        async function poll() {
            if (stopped) return;
            try {
                if (!ws || ws.readyState !== 1 || now() - lastMessage > 35000) {
                    controller = new win.AbortController();
                    const timeout = later(() => controller && controller.abort(), 6000);
                    try {
                        const response = await get(root.dataset.pollUrl, {
                            credentials: "same-origin", cache: "no-store", signal: controller.signal,
                        });
                        if (response.status === 401 || response.status === 403 || response.redirected) {
                            status.textContent = "Для обновления состояния войдите в админку";
                            stop(); return;
                        }
                        if (!response.ok) throw new Error("Runtime polling failed");
                        show(await response.json(), "Резервное обновление");
                    } finally { cancel(timeout); controller = null; }
                }
            } catch (_error) {
                if (!stopped) status.textContent = "Связь прервана — показан последний снимок";
            } finally {
                if (!stopped) pollTimer = later(poll, 5000);
            }
        }
        function ping() {
            if (stopped || !ws || ws.readyState !== 1) return;
            ws.send(JSON.stringify({type: "ping"}));
            pingTimer = later(ping, 20000);
        }
        function connect() {
            if (stopped) return;
            try {
                ws = makeSocket((win.location.protocol === "https:" ? "wss://" : "ws://") + win.location.host + root.dataset.wsPath);
            } catch (_error) { retry(); return; }
            ws.onopen = () => { backoff = 2000; pingTimer = later(ping, 20000); };
            ws.onmessage = event => {
                if (stopped) return;
                try {
                    const payload = JSON.parse(event.data);
                    if (payload.type === "runtime" || payload.type === "pong") lastMessage = now();
                    show(payload, "Прямое обновление");
                } catch (_error) { ws.close(); }
            };
            ws.onclose = event => {
                cancel(pingTimer); lastMessage = -Infinity;
                if (event.code === 4403) {
                    status.textContent = "Нет доступа к состоянию станции";
                    stop(); return;
                }
                if (!stopped) { status.textContent = "Используется резервное обновление"; retry(); }
            };
            ws.onerror = () => { status.textContent = "Используется резервное обновление"; };
        }
        function retry() {
            if (stopped) return;
            reconnectTimer = later(connect, backoff);
            backoff = Math.min(30000, backoff * 2);
        }
        function stop() {
            stopped = true;
            [pollTimer, reconnectTimer, pingTimer].forEach(cancel);
            if (controller) controller.abort();
            if (ws && ws.readyState < 2) ws.close();
            win.removeEventListener("pagehide", stop);
        }
        win.addEventListener("pagehide", stop);
        connect(); poll();
        return {stop};
    }
    return {render, mount};
});
