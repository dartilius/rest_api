//TODO: Переписать на классы

import { API_URL } from "@/src/config/api.config";
import {
  UserInfo,
  UsersListResponse,
  UsersListResponseDTO,
} from "@/src/types/interface/user.interface";
import {
  userResponseTransformer,
  userTransformer,
} from "@/src/types/transformers/users.transformers";

type Params = {
  page: number;
  limit: number;
  created_after: string;
  created_before: string;
  name: string | undefined;
};

export const UsersService = {
  async getAll(params: Params): Promise<UsersListResponse> {
    const { page, limit, created_after, created_before, name } = params;
    let url = `${API_URL}/api/users/`;

    if (page !== undefined) {
      url += `?page=${page}`;
    }
    if (limit !== undefined) {
      url += `&limit=${limit}`;
    }
    if (created_after !== undefined) {
      url += `&created_after=${created_after}`;
    }
    if (created_before !== undefined) {
      url += `&created_before=${created_before}`;
    }
    if (name !== undefined) {
      url += `&name=${name}`;
    }
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      const data: UsersListResponseDTO = await response.json();

      return userResponseTransformer(data);
    } else {
      throw new Error("Не удалось получить список пользователей");
    }
  },

  async getById(id: string): Promise<UserInfo> {
    const response = await fetch(`${API_URL}/api/users/${id}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      const data = await response.json();

      return userTransformer(data);
    } else {
      throw new Error("Не удалось получить пользователя");
    }
  },
};
