

export interface NomenclaturesDataList {
    id: string;
    article: string;
    name: string;
    timezone: string;
    status: string;
    last_answer: string;
    version: string;
}
export interface fetchNomenclaturesResponse {
    count: number;
    next: string;
    previous: string;
    results: NomenclaturesDataList[];
}

export interface DayConfig {
  default_volume: number[];
  worktime: string;
  custom_volume: string; // Замените на конкретный тип, если известна структура
}

export interface INomenclatureByIdResponse {
  article: number;
  hw_info: any;
  id: string;
  main_info:
    | {
        created: string;
        description: string;
        last_answer: string;
        name: string;
        owner: {
          full_name: string;
        };
        status: number;
        timezone: string;
        version: string;
      }
    | undefined;

  settings?: {
    mon: DayConfig;
    thu: DayConfig;
    wed: DayConfig;
    tue: DayConfig;
    fri: DayConfig;
    sat: DayConfig;
    sun: DayConfig;
  };
}
