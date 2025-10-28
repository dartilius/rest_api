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

export const guessType = (fileName: string) => {
    const ext = fileName.split(".").pop()

    const imageExtensions = [
        "png",
        "gif",
        "jpg",
        "ico",
        "jfif",
        "jpeg",
        "bmp",
        "tif",
        "tiff",
    ];
    const audioExtensions = ["mp3", "wav"];
    const videoExtensions = ["mp4", "mov", "avi"];

    if (ext && imageExtensions.includes(ext.toLowerCase())) return "image";
    if (ext && ["svg"].includes(ext.toLowerCase())) return "svg";
    if (ext && audioExtensions.includes(ext.toLowerCase())) return "audio";
    if (ext && videoExtensions.includes(ext.toLowerCase())) return "video";
}