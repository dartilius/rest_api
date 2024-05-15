export type NomenclatureListInterface = {
    id: string
    name: string
    timezone: string
    status: string
    last_answer: string
    version: string
}

export type NomenclatureListResponseInterface = {
    count: number
    next: string
    previous: string
    results: NomenclatureListInterface[]
}

export type RequestNomenclatureFilterStatus = {
    status: number
}

export interface SettingsInterface {
    fri: {
        default_volume: [number, number, number, number]
        worktime: [string, string]
    }
    mon: {
        default_volume: [number, number, number, number]
        worktime: [string, string]
    }
    sat: {
        default_volume: [number, number, number, number]
        worktime: [string, string]
    }
    sun: {
        default_volume: [number, number, number, number]
        worktime: [string, string]
    }
    thu: {
        default_volume: [number, number, number, number]
        worktime: [string, string]
    }
    tue: {
        default_volume: [number, number, number, number]
        worktime: [string, string]
    }
    wed: {
        default_volume: [number, number, number, number]
        worktime: [string, string]
    }
}

export interface NomenclatureInterface {
    id: string;
    owner?: string;  // Use '?' to indicate that the field can be undefined.
    name?: string;
    timezone?: string;
    is_active?: boolean;
    status?: string;
    last_answer?: string;
    version?: string;
    description?: string;
    created?: string;
    settings: SettingsInterface;
    [key: string]: any;
}
