export interface NomenclatureListResponseInterface {
    results: NomenclatureListInterface[];
    next: string
    previous: string
    count: number
}

export interface NomenclatureListInterface {
    id: string
    name: string
    timezone: string
    last_answer: string
    version: string
}

export interface NomenclatureInterface {
    created: string
    description: string
    hw_info: string
    id: string | string[] | undefined
    last_answer: string
    name: string
    settings: SettingsInterface
    status: string
    timezone: string
    version: string
}

interface SettingsInterface {
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
