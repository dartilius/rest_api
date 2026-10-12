const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const {viewFor} = require("../orders/static/orders/order_form.js");

test("background hides advertising controls and permanent background hides end date", () => {
    const state = viewFor("background", "fixed_time", true);
    assert.equal(state.ad, false);
    assert.equal(state.frequency, false);
    assert.equal(state.audio, false);
    assert.equal(state.permanent, true);
    assert.equal(state.endDate, false);
    assert.equal(viewFor("background", "workday", false).endDate, true);
});
test("each periodic mode exposes its required clocks", () => {
    for (const [policy, expected] of [
        ["workday", [false, false, false]], ["open_offset", [false, false, true]],
        ["close_offset", [false, false, true]], ["fixed_time", [true, true, false]],
        ["open_to_fixed", [false, true, false]], ["fixed_to_close", [true, false, false]],
        ["start_to_close", [true, false, false]],
    ]) {
        const state = viewFor("advertising", policy, false);
        assert.equal(state.frequency, true);
        assert.deepEqual([state.start, state.end, state.offset], expected);
    }
});
test("continuous sound policy is automatic and legacy event cannot show new settings", () => {
    const state = viewFor("advertising", "continuous", false);
    assert.equal(state.frequency, false);
    assert.equal(state.audio, true);
    assert.equal(state.automaticAudio, true);
    assert.equal(viewFor("advertising", "event", false).audio, false);
});

test("mount preserves existing audio choices and changes disable irrelevant inputs", () => {
    const fields = {}, rows = {}, listeners = {};
    for (const name of ["placement", "playback_policy", "times_in_hour", "start_time", "end_time", "offset_minutes", "offset_seconds",
        "is_permanent", "ends_at", "advertising_audio", "suppress_background_audio", "suppress_background_visual"]) {
        fields[name] = {value: "", checked: false, disabled: false,
            addEventListener: (_, callback) => { listeners[name] = callback; }};
        rows[name] = {hidden: false, querySelectorAll: () => [fields[name]]};
    }
    fields.placement.value = "advertising";
    fields.playback_policy.value = "workday";
    fields.advertising_audio.value = "sound";
    const guide = {dataset: {placement: "advertising", policy: "workday", permanent: "false"}};
    const hint = {textContent: ""};
    const document = {
        readyState: "complete",
        getElementById: id => id === "order-form-guide" ? guide : id === "order-policy-help" ? hint : fields[id.slice(3)],
        querySelector: selector => selector.startsWith(".form-row.field-") ? rows[selector.slice(16)] : {hidden: false},
    };
    vm.runInNewContext(fs.readFileSync(require.resolve("../orders/static/orders/order_form.js"), "utf8"), {document});
    assert.equal(fields.suppress_background_audio.checked, false);
    fields.playback_policy.value = "open_offset";
    listeners.playback_policy();
    assert.equal(fields.offset_minutes.required, true);
    assert.equal(fields.offset_seconds.disabled, false);
    fields.advertising_audio.value = "muted";
    listeners.advertising_audio();
    assert.equal(fields.suppress_background_audio.checked, false);
    assert.equal(fields.suppress_background_visual.checked, true);
    fields.playback_policy.value = "continuous";
    listeners.playback_policy();
    assert.equal(fields.times_in_hour.disabled, true);
    assert.equal(fields.suppress_background_visual.disabled, true);
    fields.placement.value = "background";
    fields.is_permanent.checked = true;
    listeners.placement();
    assert.equal(fields.playback_policy.value, "workday");
    assert.equal(fields.ends_at.disabled, true);
    assert.equal(fields.advertising_audio.disabled, true);
});
