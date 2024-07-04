import { API_URL } from "../../config/api.config";
import {
  GroupsListResponse,
  GroupsListResponseDTO,
} from "../../types/interface/groups.interface";
import { groupsListResponseTransformer } from "../../types/transformers/groups.transformers";

interface Pagination {
  page?: number;
  limit?: number;
}

export const GroupsService = {
  async getAll({ page, limit }: Pagination = {}): Promise<GroupsListResponse> {
    let url = `${API_URL}/api/groups/`;

    console.log(page, limit);


    if (page !== undefined) {
      url += `?page=${page}`;
    }
    if (limit !== undefined) {
      url += `&limit=${limit}`;
    }

    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      const data: GroupsListResponseDTO = await response.json();

      return groupsListResponseTransformer(data);
    } else {
      throw new Error("Не удалось получить список групп");
    }
  },
};
