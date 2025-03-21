import {API_URL} from "@/config/api.config";
import {getServerAccessToken} from "@/utils";
import {getAccessToken} from "@/services/accessToken";

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
    id: string,
    name: string,
    length: string,
    size: number,
    type: number
}

export async function fetchFilesList(props: fetchFilesListQuery): Promise<fetchFilesResponse> {
    const token = await getServerAccessToken();
    const {file_type, page, tags, name, limit} = props;
    // console.log('token', token)
    console.log('url', `${API_URL}files/?page=${page}&limit=${limit}&name=${name}`)
    try {
        const response = await fetch(`${API_URL}files/?page=${page}&limit=${limit}&name=${name}`, {
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

type fetchFilesByIdQuery = {
    id: string | undefined;
}

type fetchFileResponse = {
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
} | string

export async function fetchFilesById(props: fetchFilesByIdQuery): Promise<fetchFileResponse> {
    const token = await getServerAccessToken();
    const {id} = props;
    try {
        const response = await fetch(`${API_URL}files/${id}`, {
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

        return await response.json() as fetchFileResponse;

    } catch (error) {
        console.error('Ошибка при запросе файлов:', error);
        throw error;
    }
}

type SendFile = {
    type: number;
    source: string;
};

type SendFileResponse = {
    id: string;
    length: string;
    size: number;
    type: string;
    tags: string[];
    url: string;
    name: string;
    owner: {
        full_name: string;
    };
    hash: string;
    created: string;
} | string;

type ErrorResponse = {
    source: string[];
}

export async function sendFile(body: SendFile): Promise<SendFileResponse> {
    const token = getAccessToken();

    try {
        const response = await fetch(`${API_URL}files/`, {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': `access_token ${token}`,
            },
            method: 'POST',
            body: JSON.stringify(body)
        });

        if (!response.ok) {
            let errorMessage = `Ошибка при создании файла: статус ${response.status}`;

            try {
                const errorData: ErrorResponse = await response.json();
                if (errorData.source && errorData.source.length > 0) {
                    errorMessage += `, источник ошибки: ${errorData.source.join(', ')}`;
                }
            } catch (jsonError) {
                errorMessage += ', не удалось распарсить ошибку';
            }

            throw new Error(errorMessage);
        }

        return await response.json() as SendFileResponse;

    } catch (error: any) {
        console.error('Ошибка при создании файла:', error);
        throw error;
    }
}
