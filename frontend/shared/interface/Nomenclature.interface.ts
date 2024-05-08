export type NomenclatureInterface = {
    id: string
    name: string
    timezone: string
    status: string
    last_answer: string
    version: string
}

export type NomenclatureResponseInterface = {
    count: number
    next: string
    previous: string
    results: NomenclatureInterface[]
}

export type RequestNomenclatureFilterStatus = {
    status: number
}