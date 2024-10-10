import axios from "axios";

import axiosInstance, { getTokenStorage } from "../auth/auth.helper";

import { API_URL } from "@/src/config/api.config";
import {
  IPlaylist,
  IPlaylistsList,
} from "@/src/types/interface/playlists.interface";

type Params = {
  page: number;
  limit: number;
  search: string;
};

class PlaylistsService {
  private URL = `${API_URL}/playlists/`;
  private token = getTokenStorage();
  getAll(props: Params) {

    const { page, limit , search} = props;

    const params = new URLSearchParams();

    if (page !== undefined) {
      params.append("page", page.toString());
    }
    if (limit !== undefined) {
      params.append("limit", limit.toString());
    }
    if (search !== undefined) {
      params.append("name", search.toString());
    }

    const queryString = params.toString();
    const urlWithParams = `${this.URL}?${queryString}`;

    return axiosInstance.get<IPlaylistsList>(`${urlWithParams}`);
  }

  async getById(id: string) {
    const {data} = await axiosInstance.get<IPlaylist>(`${this.URL}${id}/`);
    return data
  }

  deleteById(id: number) {
    return axiosInstance.delete(`${this.URL}${id}/`);
  }

  patchById(id: string, data: any) {
    return axiosInstance.patch(`${this.URL}${id}/`, data);
  }

  updateById(id: number, data: any) {
    return axiosInstance.put(`${this.URL}${id}/`, data);
  }

  create(data: any) {
    return axiosInstance.post(`${this.URL}`, data);
  }
}

export default new PlaylistsService();