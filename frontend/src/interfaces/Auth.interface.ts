export interface IAuth {
  email: string;
  password: string;
}

export interface IAuthResponse {
  access: string;
  refresh: string;
}

export interface IRefreshCreate {
  refresh: string;
}

export interface IRefreshCreateResponse {
  access: string;
  refresh: string;
}

export interface IAccessCreate {
  access: string;
}

export interface IAccessCreateResponse {
  access: string;
}
