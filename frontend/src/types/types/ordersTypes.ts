const ordersTypes: Order = {
    0: 'Фоновая музыка',
    1: 'Фоновые видео',
    2: 'Фоновые картинки',
    3: 'Бегущая строка'
}

type Order = {
    [key: number]: string;
}

export function convertOrdersTypes(ordersId: number | undefined): string {
    if (ordersId === undefined) {
        return "Undefined Order";
    }

    if (ordersId in ordersTypes) {
        return ordersTypes[ordersId];
    } else {
        throw new Error(`Unknown Order ID: ${ordersId}`);
    }
}
