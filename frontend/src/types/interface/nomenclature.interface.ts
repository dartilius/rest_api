export interface NomenclatureListResponseInterface {
  results: NomenclatureInterfaceList[];
  next: string;
  previous: string;
  count: number;
}

export interface NomenclatureInterfaceList {
  id: string;
  last_answer: string;
  name: string;
  status: number | null;
  timezone: string;
  version: string;
}

export interface NomenclatureInterface {
  id: string;
  main_info: {
    created: string;
    description: string;
    last_answer: string;
    name: string;
    owner: string;
    status: number | null;
    timezone: string;
    version: string;
  }
  settings: SettingsInterface;
}

// export interface NomenclatureInterface {
//   created: string;
//   description: string;
//   hw_info: string | null;
//   id: string;
//   last_answer: string;
//   name: string;
//   settings: SettingsInterface;
//   status: number;
//   timezone: string;
//   version: string;
//   owner: string;
// }

export interface SettingsInterface {
  fri?: DaySettings;
  mon?: DaySettings;
  sat?: DaySettings;
  sun?: DaySettings;
  thu?: DaySettings;
  tue?: DaySettings;
  wed?: DaySettings;
  [key: string]: DaySettings | undefined;
}

export interface DaySettings {
  worktime: [string, string];
  default_volume: [number, number, number, number];
}

export interface NomenclatureCreateInterface {
  name: string;
  timezone: string;
  description: string;
  settings: SettingsInterface;
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
