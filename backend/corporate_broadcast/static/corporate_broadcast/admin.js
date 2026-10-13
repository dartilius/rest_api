'use strict';
document.addEventListener('click', function (event) {
    const link = event.target.closest('[data-cb-edit-brand]');
    if (!link || !window.showRelatedObjectPopup) return;
    event.preventDefault();
    // Django's popup protocol updates the existing M2M selectors on save.
    window.showRelatedObjectPopup({id: 'change_id_logo_brands', href: link.href});
});
