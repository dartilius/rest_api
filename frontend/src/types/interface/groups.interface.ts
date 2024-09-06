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

export interface GroupDetailsResponse {
  id: number;
  name: string;
  description: string;
  owner: string;
  created: string;
  clients: GroupClients[];
}

export interface GroupClients {
  id: string;
  name: string;
}