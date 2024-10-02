const TIMEZONES = {
  "": "Все",
  "Etc/GMT+11": "UTC -11",
  "Etc/GMT+10": "UTC -10",
  "Etc/GMT+9": "UTC -9",
  "Etc/GMT+8": "UTC -8",
  "Etc/GMT+7": "UTC -7",
  "Etc/GMT+6": "UTC -6",
  "Etc/GMT+5": "UTC -5",
  "Etc/GMT+4": "UTC -4",
  "Etc/GMT+3": "UTC -3",
  "Etc/GMT+2": "UTC -2",
  "Etc/GMT+1": "UTC -1",
  "Etc/GMT+0": "UTC",
  "Etc/GMT-1": "UTC +1",
  "Etc/GMT-2": "UTC +2",
  "Etc/GMT-3": "UTC +3",
  "Etc/GMT-4": "UTC +4",
  "Etc/GMT-5": "UTC +5",
  "Etc/GMT-6": "UTC +6",
  "Etc/GMT-7": "UTC +7",
  "Etc/GMT-8": "UTC +8",
  "Etc/GMT-9": "UTC +9",
  "Etc/GMT-10": "UTC +10",
  "Etc/GMT-11": "UTC +11",
  "Etc/GMT-12": "UTC +12",
};

export const timezonesArray = Object.keys(TIMEZONES).map((key) => ({
  value: key,
  label: TIMEZONES[key as keyof typeof TIMEZONES],
}));


const types: Types = {
  "UTC +2": "UTC +2 Калининград",
  "UTC +3": "UTC +3 Москва",
  "UTC +4": "UTC +4 Самара",
  "UTC +5": "UTC +5 Екатеринбург",
  "UTC +6": "UTC +6 Омск",
  "UTC +7": "UTC +7 Красноярск",
  "UTC +8": "UTC +8 Иркутск",
  "UTC +9": "UTC +9 Якутск",
  "UTC +10": "UTC +10 Владивосток",
  "UTC +11": "UTC +11 Магадан",
  "UTC +12": "UTC +12 CumЧатка",
};

type Types = {
  [key: string]: string;
};

export function convertZone(statusId: string): string {
  if (statusId === undefined) {
    return "Undefined Status";
  }

  if (statusId in types) {
    return types[statusId];
  } else {
    throw new Error(`Unknown status ID: ${statusId}`);
  }
}
