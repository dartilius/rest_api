import { ITokens } from "@/shared/interface/user.interface";
import Cookies from 'js-cookie'

export const saveTokensStorage = (data: ITokens) => {
    Cookies.set("accessToken", data.accessToken);
    Cookies.set("refreshToken", data.refreshToken);
}

export const saveToStorage = (data: ITokens) => {
    saveToStorage(data)
}

export const removeTokensStorage = () => {
    Cookies.remove('accessToken')
    Cookies.remove('refreshToken')
}