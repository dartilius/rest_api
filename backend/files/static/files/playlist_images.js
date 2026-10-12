"use strict";
document.addEventListener("formset:added", event => {
    if (!event.detail || event.detail.formsetName !== "items") return;
    const position = event.target.querySelector('input[name$="-position"]');
    if (!position) return;
    const others = [...document.querySelectorAll('input[name$="-position"]')]
        .filter(input => input !== position && !input.closest(".empty-form"))
        .map(input => Number(input.value)).filter(Number.isFinite);
    position.value = others.length ? Math.max(...others) + 1 : 0;
});
