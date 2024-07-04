export type GroupsListResponseDTO = {
  count: number;
  next: string | null;
  previous: string | null;
  results: GroupsListDTO[];
};

export type GroupsListDTO = {
  id: number;
  name: string;
  created: string;
  clients_count: number;
};

export type GroupsListResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: GroupsList[];
};

export type GroupsList = {
  id: number;
  name: string;
  created: string;
  clientsCount: number;
};