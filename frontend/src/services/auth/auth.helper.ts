import Cookies from "js-cookie";

import { ITokens } from "@/src/types/interface/user.interface";
import { IAuthResponse } from "@/src/store/user/user.interface";

export const saveTokensStorage = (data: ITokens) => {
  localStorage.setItem("access", data.access);
  Cookies.set("access", data.access);
  localStorage.setItem("refresh", data.refresh);
  Cookies.set("refresh", data.refresh);
};

export const saveToStorage = (data: IAuthResponse) => {
  saveTokensStorage(data); // Изменено с saveToStorage на saveTokensStorage
  localStorage.setItem("user", JSON.stringify(data.user));
};

export const removeTokensStorage = () => {
  Cookies.remove("access");
  Cookies.remove("refresh");
};

export const getTokenStorage = () => {
  return localStorage.getItem("access");
};
