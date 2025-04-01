import {API_URL} from "@/config/api.config";
import {getClientAccessToken, getServerAccessToken} from "@/utils";
import {getAccessToken} from "@/services/accessToken";
import {redirect} from "next/navigation";
import {IFilesListResponse} from "@/types/fileTypes";
import {client} from "@/services/httpClient";

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
    type: string
}

const isSSR = typeof window === "undefined";

export async function getFilesList(queryParams: {
    page: number;
    limit: number;
    name: string;
    file_type: string;
}): Promise<IFilesListResponse> {
    let token;
    if (isSSR) {
        token = await getServerAccessToken();
    } else {
        token = getClientAccessToken()
    }

    const stringifiedQueryParams = {
        ...queryParams,
        page: queryParams.page.toString(),
        limit: queryParams.limit.toString(),
        name: queryParams.name.toString(),
        file_type: queryParams.file_type.toString(),
    }

    const url = `${API_URL}files`

    return await client.get<IFilesListResponse>(url, {
        params: stringifiedQueryParams,
        headers: {
            Authorization: `access_token ${token}`
        }
    })
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
    hash: string;
    created: string;
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

export async function deleteFile(id: string): Promise<any> {
    const token = getAccessToken()
    try {
        const response = await fetch(`${API_URL}files/${id}/`, {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': `access_token ${token}`,
            },
            method: 'DELETE',
        });

        if (!response.ok) {
            let errorMessage = `Ошибка при удалении файла: статус ${response.status}`;

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
        return response;

    } catch (error: any) {
        console.error('Ошибка при удалении файла:', error);
        throw error;
    }
}
