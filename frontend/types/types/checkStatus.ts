const types: Types = {
  0: "Онлайн",
  1: "Оффлайн 5 минут",
  2: "Оффлайн час",
  3: "Все",
};

type Types = {
  [key: number]: string;
};

export function convertStatus(statusId: number | undefined): string {
  if (statusId === undefined) {
    return "Undefined Status";
  }

  if (statusId in types) {
    return types[statusId];
  } else {
    throw new Error(`Unknown status ID: ${statusId}`);
  }
}
