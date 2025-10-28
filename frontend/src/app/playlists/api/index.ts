import { PaginatedResponse } from "@/components/Ui/AsyncAutocomplete";
import { API_URL } from "@/config/api.config";
import { client } from "@/services/httpClient";
import { IDataPlayListsResponse, IPlayList, IPlayListsDetail} from "@/types/playListsTypes";
import { getToken } from "@/utils";

export async function getPlayLists(params: {
  page: number;
  search: string;
  id?: string;
  limit?: number;
}): Promise<PaginatedResponse<IPlayList>> {
  const token = await getToken();
  
  const response = await client.get<IDataPlayListsResponse>(
    `${API_URL}playlists`, 
    {
      params: {
        page: params.page,
        limit: params.limit,
        name: params.search,
        id: params.id || ''
      },
      headers: {
        Authorization: `access_token ${token}`,
      }
    }
  );

  return {
    results: response.results,
    count: response.count,
  };
}


export async function getPlayListDetail(id: string): Promise<IPlayListsDetail> {
    try {
      const token = await getToken()
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

  