export type TagsListResponseDTO = {
  count: number;
  next: string;
  previous: string;
  results: TagResponseDTO[];
};

export type TagsListResponse = {
  count: number;
  next: string;
  previous: string;
  results: TagResponse[];
};

export type TagResponseDTO = {
  id: number;
  name: string;
};

export type TagResponse = {
  id: number;
  name: string;
};
