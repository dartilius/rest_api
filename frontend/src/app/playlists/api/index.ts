import { API_URL } from "@/config/api.config";
import { client } from "@/services/httpClient";
import { IDataPlayListsResponse, IPlayListsDetail} from "@/types/playListsTypes";

import { getServerAccessToken, getClientAccessToken } from "@/utils";

const isSSR = typeof window === "undefined";
console.log('isSsr', isSSR);


export async function getPlayLists(queryParams: {
    id: string
    page: number;
    limit: number;
    name: string;
}): Promise<IDataPlayListsResponse> {
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
        id: queryParams.id.toString(),
        page: queryParams.page.toString(),
        limit: queryParams.limit.toString(),
        name: queryParams.name.toString(),
    };

    const url = `${API_URL}playlists`;

    const res = await client.get<IDataPlayListsResponse>(url, {
        params: stringifiedQueryParams,
        headers: {
            Authorization: `access_token ${token}`,
        }
    });
console.log(res);

    return res; 
}


export async function getPlayListDetail(id: string): Promise<IPlayListsDetail> {
    try {
      const token = await getServerAccessToken();
      const url = `${API_URL}playlists/${id}`;
  
      const res = await client.get<IPlayListsDetail>(url, {
        headers: {
          Authorization: `access_token ${token}`,
        }
      });
  
      if (!res) {
        throw new Error('getPlayListDetail not found');
      }
  
      return res;
    } catch (error) {
      console.error('Error fetching getPlayListDetail:', error);
      throw error;
    }
  }

  