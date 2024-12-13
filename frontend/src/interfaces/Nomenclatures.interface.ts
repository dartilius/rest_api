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
  status: string;
}

export interface INomenclaturesService {
  token: string | null;
  page: number;
  limit: number;
  timezone?: string;
  status?: string;
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

  settings: {
    mon: {
      default_volume: number[];
      worktime: string;
      custom_volume: any;
    };
    thu: {
      default_volume: number[];
      worktime: string;
      custom_volume: any;
    };
    wed: {
      default_volume: number[];
      worktime: string;
      custom_volume: any;
    };
    tue: {
      default_volume: number[];
      worktime: string;
      custom_volume: any;
    };
    fri: {
      default_volume: number[];
      worktime: string;
      custom_volume: any;
    };
    sat: {
      default_volume: number[];
      worktime: string;
      custom_volume: any;
    };
    sun: {
      default_volume: number[];
      worktime: string;
      custom_volume: any;
    };
  };
}
