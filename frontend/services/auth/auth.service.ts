import axios, { AxiosResponse } from "axios";

import { removeTokensStorage, saveTokensStorage } from "./auth.helper";

import { ITokens } from "../../types/interface/user.interface";
import { API_URL } from "../../config/api.config";

export const AuthService = {
  async login(
    email: string,
    password: string,
  ): Promise<AxiosResponse<ITokens>> {
    const response = await axios.post<ITokens>(
      `${API_URL}/auth/jwt/create`,
      {
        email,
        password,
      },
      {
        headers: {
          Allow: "POST, OPTIONS",
          "Content-Type": "application/json",
          Vary: "Accept",
        },
      },
    );

    if (response.data.access) {
      console.log(JSON.stringify(response.data));

      saveTokensStorage(response.data);
    }

    return response;
  },

  logout() {
    removeTokensStorage();
    localStorage.clear();
  },

  async isAuthenticated(req: any): Promise<boolean> {
    const token = req.cookies["accessToken"]; // получение токена из кук

    return !!token;
  },
};
