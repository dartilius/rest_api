export type PlaylistsListResponseDTO = {
  count: number;
  next: string | null;
  previous: string | null;
  results: PlaylistsListDTO[];
};

export type PlaylistsListDTO = {
  id: number;
  name: string;
  created: string;
  files_count: number;
};

export type PlaylistsListResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: PlaylistsList[];
};

export type PlaylistsList = {
  id: number;
  name: string;
  created: string;
  filesCount: number;
};
