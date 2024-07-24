//TODO: Переписать на классы

import axios, { AxiosResponse } from "axios";

import { removeTokensStorage, saveTokensStorage } from "./auth.helper";

import { ITokens } from "@/src/types/interface/user.interface";
import { AUTH_URL } from "@/src/config/api.config";

export const AuthService = {
  async login(
    email: string,
    password: string,
  ): Promise<AxiosResponse<ITokens>> {
    const response = await axios.post<ITokens>(
      `${AUTH_URL}/jwt/create`,
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
