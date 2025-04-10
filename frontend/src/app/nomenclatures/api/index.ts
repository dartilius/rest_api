import {getClientAccessToken, getServerAccessToken} from "@/utils";
import {API_URL} from "@/config/api.config";
import {client, HttpClient} from "@/services/httpClient";
import {
    fetchNomenclaturesResponse,
    INomenclatureByIdResponse, NomenclaturesDataList,
    NomenclaturesListProps
} from "@/interfaces/Nomenclatures.interface";

const defaultHeaders = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}

const isSSR = typeof window === "undefined";
console.log('isSsr', isSSR);

const getToken = async () => {
    const isSSR = typeof window === 'undefined'
    let token
    if (isSSR) {
        token = await getServerAccessToken()
    } else {
        token = getClientAccessToken()
    }

    return token
}


export async function  getNomenclaturesList(queryParams: { searchParams?: Promise<NomenclaturesListProps> }): Promise<fetchNomenclaturesResponse> {
    const token = await getToken();
    console.log('token', token)
    const resolvedParams = await queryParams.searchParams || {};
    const strQueryParams = {
        ...resolvedParams,
        page: Number(resolvedParams.page || 1),
        limit: Number(resolvedParams.limit || 10),
    };

    const url = `${API_URL}nomenclatures/`;

    return client.get<fetchNomenclaturesResponse>(url, {
        params: strQueryParams,
        headers: {
            Authorization: `access_token ${token}`,
        },
    });
}

export class NomenclaturesService extends HttpClient {
    private async getAuthToken(): Promise<string | null> {
        return isSSR ? await getServerAccessToken() : getClientAccessToken();
    }



    async getNomenclatureById(id: string): Promise<INomenclatureByIdResponse> {
        const token = await this.getAuthToken();
        const url = `${API_URL}/nomenclatures/${id}/`;

        return this.get<INomenclatureByIdResponse>(url, {
            headers: {
                ...defaultHeaders,
                Authorization: `access_token ${token}`,
            },
        });
    }

    async createNomenclature(data: NomenclaturesDataList): Promise<NomenclaturesDataList> {
        const token = await this.getAuthToken();
        const url = `${API_URL}/nomenclatures/`;

        return this.post<NomenclaturesDataList>(url, {
            body: data,
            headers: {
                ...defaultHeaders,
                Authorization: `access_token ${token}`,
            },
        });
    }

    async deleteNomenclature(id: string) {
        const token = await this.getAuthToken();
        const url = `${API_URL}nomenclatures/${id}/`;

        return this.delete(url, {
            headers: {
                ...defaultHeaders,
                Authorization: `access_token ${token}`,
            },
        });
    }

}

export const nomenclaturesService = new NomenclaturesService();