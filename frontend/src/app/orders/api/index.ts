import { client } from "@/services/httpClient";
import { getServerAccessToken, getClientAccessToken } from "@/utils";

const isSSR = typeof window === "undefined";
console.log('isSsr', isSSR);

export async function getDataBg(queryParams: {
    page: number;
    limit: number;
    name: string;
    status: string;
    timezone: string;
    version: string;
}): Promise<any> {
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
        page: queryParams.page.toString(),
        limit: queryParams.limit.toString()
    };

    const url = `${process.env.NEXT_PUBLIC_API_URL}/api/bgorders`;

    const res = await client.get<any>(url, {
        params: stringifiedQueryParams,
        headers: {
            Authorization: `access_token ${token}`,
        }
    });

    return res; 
}
