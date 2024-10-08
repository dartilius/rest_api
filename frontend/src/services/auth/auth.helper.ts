import Cookies from "js-cookie";

import { ITokens } from "@/src/types/interface/user.interface";
import { IAuthResponse } from "@/src/store/user/user.interface";

export const saveTokensStorage = (data: ITokens) => {
  localStorage.setItem("access_admin", data.access);
  Cookies.set("access_admin", data.access);
  localStorage.setItem("refresh_admin", data.refresh);
  Cookies.set("refresh_admin", data.refresh);
};

export const saveToStorage = (data: IAuthResponse) => {
  saveTokensStorage(data); // Изменено с saveToStorage на saveTokensStorage
  localStorage.setItem("user", JSON.stringify(data.user));
};

export const removeTokensStorage = () => {
  Cookies.remove("access_admin");
  Cookies.remove("refresh_admin");
};

export const getTokenStorage = () => {
  return Cookies.get("access_admin");
};
