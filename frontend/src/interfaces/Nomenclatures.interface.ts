export interface INomenclaturesResponse {
  count: number;
  next: string;
  previous: string;
  results: INomenclatureResults[];
}

export interface INomenclatureResults {
  id: number;
  name: string;
  timezone: string;
  version: string;
  last_answer: string;
  status: number;
}

export interface INomenclaturesService {
  page: number;
  limit: number;
  timezone: string;
  status: string;
  search: string;
  version: string;
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
