import { API_URL } from "../../config/api.config";
import {
  TagsListResponse,
  TagsListResponseDTO,
} from "../../types/interface/tags.interface";
import { tagsListResponseTransformer } from "../../types/transformers/tags.trasformer";

export const TagsService = {
  async gatAll(): Promise<TagsListResponse> {
    const response = await fetch(`${API_URL}/api/tags/`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      const data: TagsListResponseDTO = await response.json();

      return tagsListResponseTransformer(data);
    } else {
      throw new Error("Не удалось получить список тэгов");
    }
  },
};
