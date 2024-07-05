export interface ITokens {
  access: string;
  refresh: string;
}

export interface IAuthInput {
  email: string;
  password: string;
}

export type UsersListResponseDTO = {
  count: number;
  next: string | null;
  previous: string | null;
  results: UsersListDTO[];
};

export type UsersListDTO = {
  id: string;
  created: string;
  full_name: string;
};

export type UsersListResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: UsersList[];
};

export type UsersList = {
  id: string;
  created: string;
  fullName: string;
};
