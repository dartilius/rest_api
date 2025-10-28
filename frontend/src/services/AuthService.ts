import { AUTH_URL } from "@/config/api.config";
import {
  IAccessCreate,
  IAccessCreateResponse,
  IAuth,
  IAuthResponse,
  IRefreshCreate,
  IRefreshCreateResponse,
} from "@/interfaces/Auth.interface";
import axios from "axios";

class AuthService {
  private URL = AUTH_URL;

  constructor() {}

  login({ email, password }: IAuth) {
    return axios.post<IAuthResponse>(`${this.URL}jwt/create/`, {
      email,
      password,
    });
  }

  logout() {
    return axios.post(`${this.URL}logout/`);
  }

  refreshCreate({ refresh }: IRefreshCreate) {
    return axios.post<IRefreshCreateResponse>(`${this.URL}jwt/refresh/`, {
      refresh,
    });
  }

  accessCreate({ access }: IAccessCreate) {
    return axios.post<IAccessCreateResponse>(`${this.URL}jwt/verify/`, {
      token: access,
    });
  }
}

export default new AuthService();
