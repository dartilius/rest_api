import { API_URL } from "../../config/api.config";
import {
  UsersListResponse,
  UsersListResponseDTO,
} from "../../types/interface/user.interface";
import { userResponseTransformer } from "../../types/transformers/users.transformers";

export const UsersService = {
  async getAll(): Promise<UsersListResponse> {
    const response = await fetch(`${API_URL}/api/users/`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      const data: UsersListResponseDTO = await response.json();
        console.log(data);

      return userResponseTransformer(data);
    } else {
      throw new Error("Не удалось получить список пользователей");
    }
  },
};
