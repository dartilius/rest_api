import Cookies from "js-cookie";

import { IAuthResponse } from "../../store/user/user.interface";
import { ITokens } from "../../types/interface/user.interface";

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
  // console.log('3', localStorage.getItem("access"));
  return localStorage.getItem("access");
};
