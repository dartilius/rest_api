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

export interface IPlaylistsList {
  count: number;
  next: string | null;
  previous: string | null;
  results: IPlaylistsListResults[];
}

interface IPlaylistsListResults {
  id: number;
  name: string;
  created: string;
  files_count: number;
}

export interface IPlaylist {
  id: number
  name: string
  description: string
  owner: string
  files: IPlaylistFiles[]
  created: string
}

export interface IPlaylistFiles {
  id: string;
  name: string;
  url: string;
}