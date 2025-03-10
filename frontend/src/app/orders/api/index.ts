import { API_URL } from "@/config/api.config";
import { client } from "@/services/httpClient";
import { IDataAdResponse, IDataBgResponse } from "@/types/orderTypes";
import { getServerAccessToken, getClientAccessToken } from "@/utils";

const isSSR = typeof window === "undefined";
console.log('isSsr', isSSR);

export async function getDataBg(queryParams: {
    pageBg: number;
    limit: number;
    name: string;
    status: string;
    timezone: string;
    version: string;
}): Promise<IDataBgResponse> {
    let token;
    if (isSSR) {
        // Для SSR получаем токен с сервера
        token = await getServerAccessToken();
        console.log('token isSsr', token);
    } else {
        // Для клиента получаем токен с клиента
        token = getClientAccessToken();
        console.log('token !isSsr', token);
    }


    const stringifiedQueryParams = {
        ...queryParams,
        page: queryParams.pageBg.toString(),
        limit: queryParams.limit.toString()
    };

    const url = `${API_URL}bgorders`;

    const res = await client.get<IDataBgResponse>(url, {
        params: stringifiedQueryParams,
        headers: {
            Authorization: `access_token ${token}`,
        }
    });

    return res; 
}
export async function getDataAd(queryParams: {
    pageAd: number;
    limit: number;
    name: string;
    status: string;
    timezone: string;
    version: string;
}): Promise<IDataAdResponse> {
    let token;
    if (isSSR) {
        // Для SSR получаем токен с сервера
        token = await getServerAccessToken();
        console.log('token isSsr', token);
    } else {
        // Для клиента получаем токен с клиента
        token = getClientAccessToken();
        console.log('token !isSsr', token);
    }


    const stringifiedQueryParams = {
        ...queryParams,
        page: queryParams.pageAd.toString(),
        limit: queryParams.limit.toString()
    };

    const url = `${API_URL}adorders`;

    const res = await client.get<IDataAdResponse>(url, {
        params: stringifiedQueryParams,
        headers: {
            Authorization: `access_token ${token}`,
        }
    });

    return res; 
}
