import Cookies from "js-cookie";

import { ITokens } from "@/src/types/interface/user.interface";
import { IAuthResponse } from "@/src/store/user/user.interface";

export const saveTokensStorage = (data: ITokens) => {
  // Устанавливаем токены в localStorage
  localStorage.setItem("access", data.access);
  localStorage.setItem("refresh", data.refresh);

  // Устанавливаем токены в cookies с дополнительными атрибутами безопасности
  Cookies.set("access", data.access, {
    secure: true, // Передача только через HTTPS
    sameSite: "Strict" // Предотвращает отправку cookie с внешних сайтов
  });
  Cookies.set("refresh", data.refresh, {
    secure: true,
    sameSite: "Strict"
  });
};

export const saveToStorage = (data: IAuthResponse) => {
  saveTokensStorage(data);
  localStorage.setItem("user", JSON.stringify(data.user));
};

export const removeTokensStorage = () => {
  Cookies.remove("access");
  Cookies.remove("refresh");
};

export const getTokenStorage = () => {
  return Cookies.get("access");
};
