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
  role: string;
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
  role: string;
};

export type UserInfoDTO = {
  id: string;
  role: string;
  email: string;
  phone_number: string;
  created: string;
  full_name: FullNameUserDTO;
};

export type UserInfo = {
  id: string;
  role: string;
  email: string;
  phoneNumber: string;
  created: string;
  fullName: FullNameUser;
};

type FullNameUser = {
  firstName: string
  lastName: string
  middleName?: string
}

type FullNameUserDTO = {
  first_name: string
  last_name: string
  middle_name?: string
}