export interface NomenclaturesListProps {
    page?: number | string;
    limit?: number | string;
    name?: string;
    status?: string;
    timezone?: string;
    version?: string;
}

interface INomenclatures {
    id: string;
    article: string;
    last_answer: string;
    name: string;
    status: string;
    timezone: string;
    version: string;
}

export interface INomenclaturesListResponse {
    count: number;
    next: string;
    previous: string;
    results: INomenclatures[]
}

interface INomenclatureMainInfo {
    created: string;
    description: string;
    last_answer: string;
    name: string;
    owner: {
        full_name: string;
    }
    status: number;
    timezone: string;
    version: string;
}

interface ISettingsOfDay {
    default_volume: [number, number, number, number];
    worktime: string;
    custom_volume?: {
        [timeRange: string]: [number, number, number, number];
    };
}

interface INomenclatureSettings {
    [day: string]: ISettingsOfDay;
}

interface INomenclatureHwInfo {
    audiodevices: Array<{
        card: number;
        name: string;
    }>

    interfaces: Array<{
        iface: string;
        ip: string;
        mac: string;
    }>

    model: string;
    revision: string;
    serial_number: string;
    sd_card_data: {
        manf_id: string;
        name: string;
    }
}

export interface INomenclatureResponse {
    id: string;
    article: string;
    hw_info: INomenclatureHwInfo;
    main_info: INomenclatureMainInfo;
    settings: INomenclatureSettings;
}

interface ICreateNomenclatureSettings {
    [day: string]: {
        worktime: string;
        default_volume: [number, number, number, number];
        custom_volume?: {
            [timeRange: string]: [number, number, number, number];
        }

    }
}

export interface ICreateNomenclature {
    name: string;
    description: string;
    version: string;
    settings: ICreateNomenclatureSettings;
}

export interface IUpdateNomenclature {
    name: string;
    description: string;
    timezone: string;
    settings: INomenclatureSettings;
}

export interface INomenclatureStatusHistoryResponse {
    change_time: string;
    status: number;
}

//типы для статистики видео и музыки, ответ у них одинаковый
export interface INomenclatureStatistics {
    length: number;
    file: string;
    played: string;
}

export interface INomenclatureStatisticsResponse {
    count: number;
    next: string;
    previous: string;
    results: INomenclatureStatistics[]
}

