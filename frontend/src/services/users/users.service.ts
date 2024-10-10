//TODO: Переписать на классы

import axios from "axios";

import axiosInstance, { getTokenStorage } from "../auth/auth.helper";

import { API_URL } from "@/src/config/api.config";
import { IUsersCreate, IUsersList, IUsersRead } from "@/src/types/interface/user.interface";

type Params = {
  page?: number;
  limit?: number;
  created_after?: string;
  created_before?: string;
  name?: string | undefined;
};

class UsersService {
  private URL = `${API_URL}/users`;
  private token = getTokenStorage();

  getAll(props: Params) {
    const { page, limit, name, created_after, created_before } = props;

    const params = new URLSearchParams();

    if (page !== undefined) {
      params.append("page", page.toString());
    }
    if (limit !== undefined) {
      params.append("limit", limit.toString());
    }
    if (name !== undefined) {
      params.append("name", name);
    }
    if (created_after !== undefined) {
      params.append("created_after", created_after);
    }
    if (created_before !== undefined) {
      params.append("created_before", created_before);
    }

    const queryString = params.toString();
    const urlWithParams = `${this.URL}?${queryString}`;

    return axiosInstance.get<IUsersList>(urlWithParams);
  }

  create(data: any) {
    return axiosInstance.post<IUsersCreate>(`${this.URL}/`, data);
  }

  getById(id: string) {
    return axiosInstance.get<IUsersRead>(`${this.URL}/${id}`);
  }

  deleteById(id: string) {
    return axiosInstance.delete(`${this.URL}/${id}`);
  }

  updateById(id: string, data: any) {
    return axiosInstance.patch(`${this.URL}/${id}/`, data);
  }
}

export default new UsersService();