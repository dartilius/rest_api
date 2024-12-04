import { AUTH_URL } from "@/src/config/api.config";
import { IAuthInput, ITokens } from "@/src/types/interface/user.interface";
import axios from "axios";

class AuthService {
  private URL = `${AUTH_URL}`;

  login = ({ email, password }: IAuthInput) =>
    axios.post<ITokens>(`${this.URL}jwt/create/`, { email, password });

  logout = () => axios.post(`${this.URL}logout/`);

  refreshTokenCreate = (refreshToken: string) =>
    axios.post<ITokens["access"]>(`${this.URL}jwt/refresh/`, {
      refreshToken,
    });

  verifyToken(accessToken: string) {
    const res = axios.post(`${this.URL}jwt/verify/`, { token: accessToken });
    return res;
  }
}

export default new AuthService();
