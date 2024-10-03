import axios from "axios";

import { getTokenStorage } from "../auth/auth.helper";

import { API_URL } from "@/src/config/api.config";
import {
  IPlaylist,
  IPlaylistsList,
} from "@/src/types/interface/playlists.interface";

type Params = {
  page?: number;
  limit?: number;
};

class PlaylistsService {
  private URL = `${API_URL}/playlists/`;
  private token = getTokenStorage();
  getAll(props: Params) {

    const { page, limit } = props;

    const params = new URLSearchParams();

    if (page !== undefined) {
      params.append("page", page.toString());
    }
    if (limit !== undefined) {
      params.append("limit", limit.toString());
    }

    const queryString = params.toString();
    const urlWithParams = `${this.URL}?${queryString}`;

    return axios.get<IPlaylistsList>(`${urlWithParams}`, {
      headers: {
        Authorization: `access_token ${this.token}`,
      },
    });
  }

  async getById(id: string) {
    const {data} = await axios.get<IPlaylist>(`${this.URL}${id}/`, {
      headers: {
        Authorization: `access_token ${this.token}`,
      },
    });
    return data
  }

  deleteById(id: string) {
    return axios.delete(`${this.URL}${id}/`, {
      headers: {
        Authorization: `access_token ${this.token}`,
      },
    });
  }

  patchById(id: string, data: any) {
    return axios.patch(`${this.URL}${id}/`, data, {
      headers: {
        Authorization: `access_token ${this.token}`,
      },
    });
  }

  updateById(id: string, data: any) {
    return axios.put(`${this.URL}${id}/`, data, {
      headers: {
        Authorization: `access_token ${this.token}`,
      },
    });
  }

  create(data: any) {
    return axios.post(`${this.URL}`, data, {
      headers: {
        Authorization: `access_token ${this.token}`,
      },
    });
  }
}

export default new PlaylistsService();