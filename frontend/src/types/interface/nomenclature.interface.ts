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
  hw_info: HwInfo;
}

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
  worktime: string;
  default_volume: [number, number, number, number];
}

export interface HwInfo {
  audiodevices: {
    card: number;
    name: string;
  }[]
  interfaces: {
    ip: string;
    mac: string;
    iface: string;
  }[]
  model: string;
  revision: string;
  sd_card_data: {
    manf_id: string;
    name: string;
  }
  serial_number: string;
}