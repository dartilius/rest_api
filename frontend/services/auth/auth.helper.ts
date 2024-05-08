import { ITokens } from "@/shared/interface/user.interface";
import Cookies from 'js-cookie'

export const saveTokensStorage = (data: ITokens) => {
    Cookies.set("accessToken", data.access);
    Cookies.set("refreshToken", data.refresh);
}

export const saveToStorage = (data: ITokens) => {
    saveToStorage(data)
}

export const removeTokensStorage = () => {
    Cookies.remove('accessToken')
    Cookies.remove('refreshToken')
}