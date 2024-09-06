export const fileTypes = [
  { key: "", label: "Все" }, // Опция для сброса фильтра
  { key: "0", label: "Реклама" },
  { key: "1", label: "Музыка" },
  { key: "2", label: "Картинка фон" },
  { key: "3", label: "Видео фон" },
  { key: "4", label: "Бегущая строка" },
];

export const types: Types = {
  0: "Реклама",
  1: "Музыка",
  2: "Картинка фон",
  3: "Видео фон",
  4: "Бегущая строка",
};

type Types = {
  [key: number]: string;
};

export function convertType(typeId: number | undefined): string {
  if (typeId === undefined) {
    return "Undefined Type";
  }

  if (typeId in types) {
    return types[typeId];
  } else {
    throw new Error(`Unknown type ID: ${typeId}`);
  }
}
