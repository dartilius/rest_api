import {
  PlaylistsListResponse,
  PlaylistsListResponseDTO,
} from "../interface/playlists.interface";

export const playlistTransformer = (
  DTO: PlaylistsListResponseDTO,
): PlaylistsListResponse => {
  return {
    count: DTO.count,
    next: DTO.next,
    previous: DTO.previous,
    results: DTO.results.map((playlist) => ({
      id: playlist.id,
      name: playlist.name,
      created: playlist.created,
      filesCount: playlist.files_count,
    })),
  };
};
