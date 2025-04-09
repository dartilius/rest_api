export interface IFilesListResponse {
    count: number;
    next: string;
    previous: string;
    results: IFilesResult[];
}

export interface IFilesResult {
    id: string;
    name: string;
    length: string;
    size: number;
    type: number;
}

export interface  IFIleResponse {
    id: string;
    length: string;
    size: number;
    type: number;
    source: string;
    tags: Array<{
        id: string;
        name: string;
    }>
    url: string;
}

