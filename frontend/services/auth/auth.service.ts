import { API_URL } from "@/config/api.config"
import { ITokens } from "@/shared/interface/user.interface"
import axios, { AxiosResponse } from "axios"
import { removeTokensStorage, saveTokensStorage } from "./auth.helper"
import { parseCookies } from 'nookies'

export const AuthService = {
    async login(username: string, password: string): Promise<AxiosResponse<ITokens>> {
        const response = await axios.post<ITokens>(
            `http://192.168.0.180:8000/auth/jwt/create`,
            {
                username,
                password
            },
            {
                headers: {
                    'Allow': 'POST, OPTIONS',
                    'Content-Type': 'application/json',
                    'Vary': 'Accept'
                }
            }
        );
        
        if (response.data.access) {
            saveTokensStorage(response.data)
        }
        return response;
    },

    logout() {
        removeTokensStorage();
        localStorage.clear();
    },

    async isAuthenticated(req: any): Promise<boolean> {
        const token = req.cookies['accessToken']; // получение токена из кук
        return !!token;
    }
}