export function getStatusColor(statusId: number): string {
    switch (statusId) {
        case 0: return "#4caf50"; // Зеленый для онлайн
        case 1: return "#ff9800"; // Оранжевый для оффлайн 5 минут
        case 2: return "#f44336"; // Красный для оффлайн час
        default: return "#9e9e9e"; // Серый для неизвестного статуса
    }
}
