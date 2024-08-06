import axios from "axios";

import { getTokenStorage } from "../auth/auth.helper";

import { API_URL } from "@/src/config/api.config";
import {
  GroupDetailsResponse,
  GroupsListResponse,
} from "@/src/types/interface/groups.interface";

interface Pagination {
  page?: number;
  limit?: number;
}

class GroupsService {
  private URL = `${API_URL}/groups`;
  private token = getTokenStorage();

  getAll(props: Pagination = {}) {
    const params = new URLSearchParams();

    if (props.page !== undefined) {
      params.append("page", props.page.toString());
    }
    if (props.limit !== undefined) {
      params.append("limit", props.limit.toString());
    }

    const queryString = params.toString();
    const urlWithParams = `${this.URL}?${queryString}`;

    return axios.get<GroupsListResponse>(urlWithParams);
  }

  create(data: any) {
    return axios.post(`${this.URL}/`, data, {
      headers: {
        Authorization: `access_token ${this.token}`,
      },
    });
  }

  getById(id: string) {
    return axios.get<GroupDetailsResponse>(`${this.URL}/${id}`);
  }

  deleteById(id: string) {
    return axios.delete(`${this.URL}/${id}`);
  }

  updateById(id: string, data: any) {
    return axios.patch(`${this.URL}/${id}/`, data);
  }
}

export default new GroupsService();
