"use strict";
function setupPlaylistSelection() {
    const select = document.getElementById("id_files_to_add");
    const hidden = document.getElementById("id_files_to_add_order");
    if (!select || !hidden) return;
    const preview = document.createElement("ol");
    preview.setAttribute("aria-label", "Порядок добавления файлов");
    preview.setAttribute("aria-live", "polite");
    select.insertAdjacentElement("afterend", preview);
    let order;
    try {
        order = JSON.parse(hidden.value || "[]");
        if (!Array.isArray(order)) order = [];
    } catch (_) {
        order = [];
    }
    function update() {
        const selected = [...select.selectedOptions];
        const labels = new Map(selected.map(option => [option.value, option.textContent]));
        order = order.filter(value => labels.has(value));
        for (const option of selected) {
            if (!order.includes(option.value)) order.push(option.value);
        }
        hidden.value = JSON.stringify(order);
        preview.replaceChildren(...order.map(value => {
            const row = document.createElement("li");
            row.textContent = labels.get(value);
            return row;
        }));
    }
    select.addEventListener("change", update);
    select.form.addEventListener("submit", update);
    update();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupPlaylistSelection);
} else {
    setupPlaylistSelection();
}
