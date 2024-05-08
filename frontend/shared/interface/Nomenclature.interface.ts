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

export type NomenclatureInterface = {
    id: string
    owner: string
    name: string
    timezone: string
    is_active: boolean
    status: string
    last_answer: string
    version: string
    description: string
    created: string
}