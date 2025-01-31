const types: Types = {
  0: "Онлайн",
  1: "Оффлайн 5 минут",
  2: "Оффлайн час",
  3: "Все",
};
type Types = {
  [key: number]: string;
};
export function convertStatus(statusId: number | undefined | null): string {
  console.log(statusId);

  if (statusId === undefined || statusId === null) {
    return "Не в сети";
  }
  if (statusId in types) {
    return types[statusId];
  } else {
    throw new Error(`Unknown status ID: ${statusId}`);
  }
}
