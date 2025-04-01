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