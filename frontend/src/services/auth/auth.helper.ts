import Cookies from "js-cookie";

import { ITokens } from "@/src/types/interface/user.interface";
import { IAuthResponse } from "@/src/store/user/user.interface";
import axios, { AxiosInstance } from "axios";

export const saveTokensStorage = (data: ITokens) => {
  localStorage.setItem("accessToken", data.access);
  Cookies.set("accessToken", data.access);
  localStorage.setItem("refreshToken", data.refresh);
  Cookies.set("refreshToken", data.refresh);
};

export const saveToStorage = (data: IAuthResponse) => {
  saveTokensStorage(data); // Изменено с saveToStorage на saveTokensStorage
  localStorage.setItem("user", JSON.stringify(data.user));
};

export const removeTokensStorage = () => {
  Cookies.remove("accessToken");
  Cookies.remove("refreshToken");
};

export const getTokenStorage = () => {
  return localStorage.getItem("accessToken");
};

const createAxiosInstance = (): AxiosInstance => {
  const token = getTokenStorage();

  const axiosInstance = axios.create({
    headers: {
      "Content-Type": "application/json",
      Authorization: `access_token ${token}`,
    },
  });

  axiosInstance.interceptors.response.use(
    (response) => response,
    (error) => {
      if (
        typeof window !== "undefined" &&
        error.response &&
        error.response.status === 401
      ) {
        window.location.href = "/login";
      }
      return Promise.reject(error);
    }
  );

  return axiosInstance;
};

const axiosInstance = createAxiosInstance();

export default axiosInstance;
