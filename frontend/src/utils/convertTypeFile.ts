const types: Record<string, string> = {
    image: 'Изображение',
    music: 'Музыка',
    video: 'Видео',
    ticker: 'Бегущая строка',
    ad: 'Реклама',
};

export const convertTypeFile = (key: string): string => {
    return types[key] || 'Неизвестный тип';
};

const typesForSend = {
    "ad": 0,
    "music": 1,
    "image": 2,
    "video": 3,
    "ticker": 4
} as const;

type TypeKey = keyof typeof typesForSend;

export const convertTypeForSendFile = (key: string): number | string => {
    return typesForSend[key as TypeKey] ?? 'Неизвестный тип';
};
