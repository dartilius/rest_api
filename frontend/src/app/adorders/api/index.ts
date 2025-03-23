import { API_URL } from "@/config/api.config";
import { client } from "@/services/httpClient";
import { IAdOrderDetail, IDataAdResponse } from "@/types/orderTypes";
import { getServerAccessToken, getClientAccessToken } from "@/utils";

const isSSR = typeof window === "undefined";
console.log('isSsr', isSSR);

export async function getDataAd(queryParams: {
    page: number;
    limit: number;
    name: string;
    client: string;
    status: string;
    created_after: string;
    created_before: string;
    brc_type: string;
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
        page: queryParams.page.toString(),
        limit: queryParams.limit.toString(),
        name: queryParams.name.toString(),
        client: queryParams.client.toString(),
        brc_type: queryParams.brc_type.toString(),
        created_after: queryParams.created_after.toString(),
        created_before: queryParams.created_before.toString(),
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


export async function getAdOrderDetail(id: string): Promise<IAdOrderDetail> {
    try {
      const token = await getServerAccessToken();
      const url = `${API_URL}adorders/${id}`;
  
      const res = await client.get<IAdOrderDetail>(url, {
        headers: {
          Authorization: `access_token ${token}`,
        }
      });
  
      if (!res) {
        throw new Error('Order not found');
      }
  
      return res;
    } catch (error) {
      console.error('Error fetching order detail:', error);
      throw error;
    }
  }