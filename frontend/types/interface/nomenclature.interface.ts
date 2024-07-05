export interface NomenclatureListResponseInterface {
  results: NomenclatureListInterface[];
  next: string;
  previous: string;
  count: number;
}

export interface NomenclatureListInterface {
  id: string;
  name: string;
  timezone: string;
  last_answer: string;
  version: string;
  status: number;
}

export interface NomenclatureInterface {
  created: string;
  description: string;
  hw_info: string;
  id: string | string[] | undefined;
  last_answer: string;
  name: string;
  settings: SettingsInterface;
  status: string;
  timezone: string;
  version: string;
  owner: string;
}

export interface NomenclatureCreateInterface {
  name: string;
  timezone: string;
  description: string;
  settings: SettingsInterface;
}

export type Day = "mon" | "tue" | "wed" | "thu" | "fri" | "sat" | "sun";

export type DaySettings = string;

export interface SettingsInterface {
  worktime?: string;
  default_volumes?: string;
  [key: string]: DaySettings | undefined;
}

// interface SettingsInterface {
//     fri: {
//         default_volume: [number, number, number, number]
//         worktime: [string, string]
//     }
//     mon: {
//         default_volume: [number, number, number, number]
//         worktime: [string, string]
//     }
//     sat: {
//         default_volume: [number, number, number, number]
//         worktime: [string, string]
//     }
//     sun: {
//         default_volume: [number, number, number, number]
//         worktime: [string, string]
//     }
//     thu: {
//         default_volume: [number, number, number, number]
//         worktime: [string, string]
//     }
//     tue: {
//         default_volume: [number, number, number, number]
//         worktime: [string, string]
//     }
//     wed: {
//         default_volume: [number, number, number, number]
//         worktime: [string, string]
//     }
// }
