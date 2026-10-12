const test = require("node:test");
const assert = require("node:assert/strict");
const ui = require("../nomenclatures/static/nomenclatures/runtime_live.js");

class Element {
    constructor(doc, tag = "div") { this.ownerDocument = doc; this.tag = tag; this.children = []; this.style = {}; this.value = ""; }
    set textContent(value) { this.value = String(value); this.children = []; }
    get textContent() { return this.value + this.children.map(child => child.textContent).join(""); }
    set innerHTML(_value) { throw new Error("wire HTML must never be inserted"); }
    appendChild(child) { this.children.push(child); }
    replaceChildren(...children) { this.children = children; this.value = ""; }
    get firstChild() { return this.children[0]; }
    setAttribute() {}
}
function environment() {
    const doc = {createElement: tag => new Element(doc, tag)};
    const panel = new Element(doc), status = new Element(doc), updated = new Element(doc);
    const root = {dataset: {pollUrl: "/admin/runtime/", wsPath: "/ws/runtime/"}, querySelector: key => ({
        "[data-runtime-content]": panel, "[data-runtime-status]": status, "[data-runtime-updated]": updated,
    })[key]};
    const timers = new Map(), sockets = [], calls = [];
    let serial = 0, clock = 0;
    const payload = {type: "runtime", version: "frame:1", stale: false, received_at: "06.10.2026 15:00:00", content: {
        has_state: true, mode: "Фоновый контент", maintenance: "Выключен", background: [
            {name: "<script>Video</script>", type: "Видео", status: "Воспроизводится", position: "5 сек", duration: "1 мин"},
        ],
    }};
    const win = {location: {protocol: "https:", host: "admin.example"}, AbortController,
        addEventListener() {}, removeEventListener() {}};
    const dependencies = {window: win, now: () => clock,
        setTimeout: (fn, delay) => { timers.set(++serial, {fn, delay}); return serial; },
        clearTimeout: id => timers.delete(id),
        fetch: async url => { calls.push(url); return {ok: true, status: 200, json: async () => payload}; },
        makeSocket: url => {
            const socket = {url, readyState: 0, close() { this.readyState = 3; if (this.onclose) this.onclose({code: 1000}); }, send() {}};
            sockets.push(socket); return socket;
        },
    };
    return {root, doc, panel, status, updated, timers, sockets, calls, payload, dependencies,
        clock: value => { clock = value; },
        async tick(delay) { const pair = [...timers].find(([, item]) => item.delay === delay); assert.ok(pair); timers.delete(pair[0]); await pair[1].fn(); },
    };
}

test("runtime content uses text nodes and readable labels", () => {
    const env = environment();
    ui.render(env.panel, env.payload.content);
    assert.match(env.panel.textContent, /<script>Video<\/script>/);
    assert.match(env.panel.textContent, /5 сек/);
});

test("healthy WebSocket suppresses polling; close restores the reserve", async () => {
    const env = environment();
    const handle = ui.mount(env.root, env.dependencies);
    await Promise.resolve(); await Promise.resolve();
    const socket = env.sockets[0];
    assert.equal(socket.url, "wss://admin.example/ws/runtime/");
    socket.readyState = 1; socket.onopen(); socket.onmessage({data: JSON.stringify(env.payload)});
    const calls = env.calls.length;
    await env.tick(5000);
    assert.equal(env.calls.length, calls);
    socket.close();
    await env.tick(5000);
    assert.equal(env.calls.length, calls + 1);
    handle.stop();
    assert.equal(env.timers.size, 0);
});

test("permission revocation stops reconnect and reserve requests", async () => {
    const env = environment();
    const handle = ui.mount(env.root, env.dependencies);
    await Promise.resolve(); await Promise.resolve();
    env.sockets[0].onclose({code: 4403});
    assert.match(env.status.textContent, /Нет доступа/);
    assert.equal(env.timers.size, 0);
    handle.stop();
});
