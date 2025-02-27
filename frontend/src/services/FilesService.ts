import {API_URL} from "@/config/api.config";
import {getServerAccessToken} from "@/utils";

type fetchFilesListQuery = {
    page?: number;
    limit?: number;
    name?: string;
    file_type?: string;
    tags?: string;
}

export type fetchFilesResponse = {
    count: number;
    next: string;
    previous: string;
    results: FilesDataList[];
} | string

export type FilesDataList = {
    id: string;
    name: string;
    length: string;
    size: number;
    type: number;
}

export async function fetchFilesList(props: fetchFilesListQuery): Promise<fetchFilesResponse> {
    const token = await getServerAccessToken();
    const { file_type, page, tags, name, limit } = props;
    console.log('token', token)
    console.log('url', `${API_URL}files/?page=${page}&limit=${limit}&name=${name}&tags=${tags}&file_type=${file_type}`)
    try {
        const response = await fetch(`${API_URL}files/?page=${page}&limit=${limit}&name=${name}&tags=${tags}&file_type=${file_type}`, {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': `access_token ${token}`,
            },
            method: 'GET',
        });

        if (!response.ok) {
            return `Ошибка загрузки файлов: статус ${response.status}, текст: ${response.statusText}`;
        }

        return await response.json() as fetchFilesResponse;

    } catch (error) {
        console.error('Ошибка при запросе файлов:', error);
        throw error;
    }
}
