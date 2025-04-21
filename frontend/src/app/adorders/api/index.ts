import { API_URL } from "@/config/api.config";
import { client } from "@/services/httpClient";
import { AdOrderType, IAdOrderDetail, IDataAdResponse, IParamsCreateAd } from "@/types/orderTypes";
import { getServerAccessToken, getClientAccessToken } from "@/utils";
import {ICancelResponse} from "@/app/bgorders/api";

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
    since_after: string;
    since_before: string;
    until_after: string;
    until_before: string;
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

        console.log(token)
  
      const res = await client.get<IAdOrderDetail>(url, {
        headers: {
          Authorization: `access_token ${token}`,
            'Accept': 'application/json'
        },

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

export async function cancelAdOrder(id: string): Promise<ICancelResponse> {
    try {
        const token = getClientAccessToken();
        const url = `${API_URL}adorders/${id}/cancel/`;

        const res = await client.delete<ICancelResponse>(url, {
            headers: {
                Authorization: `access_token ${token}`,
                'Content-Type': 'application/json'
            },
        });
        console.log(res);

        return res;
    } catch (error) {
        console.error('Cancel error:', error);
        throw new Error('Ошибка отмены заказа');
    }
}

export async function getSelects() {
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

    try {
      const clients = await 
        client.get<{ clients: any }>(`${API_URL}nomenclatures/`,{
            headers: {
                Authorization: `access_token ${token}`,
            },
        });
        console.log(clients);

        return clients;
    } catch (error) {
        console.error('Cancel error:', error);
        throw new Error('Ошибка отмены заказа');
    }
}
interface Client {
  id: string
  name: string
}


interface ClientsResponse {
  count: number
  next: string | null
  previous: string | null
  results: Client[]
}
export async function loadClients(page: number, name: string): Promise<ClientsResponse> {
  try {
    const token = await getServerAccessToken();
    const response: ClientsResponse = await client.get(`${API_URL}nomenclatures/`, {
      params: {
        page: page.toString(),
        limit: '25', // Укажите нужное количество элементов на странице
        name: name.toString() || '',
      },
      headers: {
        Authorization: `access_token ${token}`
      }
    });
    return response;
  } catch (error) {
    console.error('Load clients error:', error);
    throw new Error('Ошибка получения клиентов/номенклатуры');
  }
}



interface AdOrderPayload {
  name: string;
  description: string;
  broadcast_type: AdOrderType;
  parameters: IParamsCreateAd;
  playlist: string[];
  clients: string[];
  broadcast_interval: {
    lower: string;
    upper: string;
  };
}

export async function createAdOrder(payload: AdOrderPayload) {

   const token = await getServerAccessToken();


  try {
    const response = await client.post(`${API_URL}adorders/`, {
      body: payload,
      headers: {
        Authorization: `access_token ${token}`
      }
    });
    
    return response;
  } catch (error) {
    console.error('Create order error:', error);
    throw new Error('Ошибка при создании заказа');
  }
}
