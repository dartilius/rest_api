//TODO: Переписать на классы

import axios from "axios";

import { getTokenStorage } from "../auth/auth.helper";

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

    return axios.get<IUsersList>(urlWithParams);
  }

  create(data: any) {
    return axios.post<IUsersCreate>(`${this.URL}/`, data, {
      headers: {
        Authorization: `access_token ${this.token}`,
      },
    });
  }

  getById(id: string) {
    return axios.get<IUsersRead>(`${this.URL}/${id}`);
  }

  deleteById(id: string) {
    return axios.delete(`${this.URL}/${id}`, {
      headers: {
        Authorization: `access_token ${this.token}`,
      },
    });
  }

  updateById(id: string, data: any) {
    return axios.patch(`${this.URL}/${id}/`, data, {
      headers: {
        Authorization: `access_token ${this.token}`,
      },
    });
  }
}

export default new UsersService();

// export const UsersService = {
//   async getAll(params: Params): Promise<UsersListResponse> {
//     const { page, limit, created_after, created_before, name } = params;
//     let url = `${API_URL}/users/`;

//     if (page !== undefined) {
//       url += `?page=${page}`;
//     }
//     if (limit !== undefined) {
//       url += `&limit=${limit}`;
//     }
//     if (created_after !== undefined) {
//       url += `&created_after=${created_after}`;
//     }
//     if (created_before !== undefined) {
//       url += `&created_before=${created_before}`;
//     }
//     if (name !== undefined) {
//       url += `&name=${name}`;
//     }
//     const response = await fetch(url, {
//       method: "GET",
//       headers: {
//         "Content-Type": "application/json",
//       },
//     });

//     if (response.ok) {
//       const data: UsersListResponseDTO = await response.json();

//       return userResponseTransformer(data);
//     } else {
//       throw new Error("Не удалось получить список пользователей");
//     }
//   },

//   async getById(id: string): Promise<UserInfo> {
//     const response = await fetch(`${API_URL}/users/${id}`, {
//       method: "GET",
//       headers: {
//         "Content-Type": "application/json",
//       },
//     });

//     if (response.ok) {
//       const data = await response.json();

//       return userTransformer(data);
//     } else {
//       throw new Error("Не удалось получить пользователя");
//     }
//   },
// };
