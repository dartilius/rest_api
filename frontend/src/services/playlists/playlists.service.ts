//TODO: Переписать на классы

import { API_URL } from "@/src/config/api.config";
import {
  PlaylistsListResponse,
  PlaylistsListResponseDTO,
} from "@/src/types/interface/playlists.interface";
import { playlistTransformer } from "@/src/types/transformers/playlists.transformer";

export const PlaylistsService = {
  async getAll(): Promise<PlaylistsListResponse> {
    const response = await fetch(`${API_URL}/api/playlists/`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      const data: PlaylistsListResponseDTO = await response.json();

      return playlistTransformer(data);
    } else {
      throw new Error("Не удалось получить список плейлистов");
    }
  },
};
