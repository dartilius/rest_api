export interface IFiles {
    id: string,
    name: string,
    length: string,
    size: number,
    type: string
}

export interface IFilesListResponse {
    count: number;
    next: string | null;
    previous: string | null;
    results: IFiles[]
}

export interface IFileDetailResponse {
    id: string;
    length: string;
    size: number;
    name: string;
    type: string;
    source: string;
    tags: Array<{
        id: string;
        name: string;
    }>
    url: string;
    hash: string;
    created: string;
}
