import { createAsyncThunk } from "@reduxjs/toolkit";
import { toastr } from "react-redux-toastr";

import { IAuthResponse, IEmailPassword, ITokens } from "./user.interface";

import { AuthService } from "../../services/auth/auth.service";
import { IAuthInput } from "../../types/interface/user.interface";
import { toastError } from "../../utils/toast-error";

// export const register = createAsyncThunk<IAuthResponse, IEmailPassword>(
//   "auth/register",
//   async ({ email, password }, thunkAPI) => {
//     try {
//       const response = await AuthService.register(email, password);

//       toastr.success("Регистрация", "Завершено успешно!");

//       return response.data;
//     } catch (error) {
//       toastError(error);

//       return thunkAPI.rejectWithValue(error);
//     }
//   },
// );

export const login = createAsyncThunk<IAuthResponse, IEmailPassword>(
  "login/",
  async ({ email, password }, thunkAPI) => {
    try {
      const response = await AuthService.login(email, password);

      // Предположим, что response.data имеет тип ITokens и нам нужно добавить user.
      const data: ITokens = response.data;
      const user: IAuthInput = { email, password }; // Или другой способ получить пользователя

      const authResponse: IAuthResponse = {
        ...data,
        user,
      };

      toastr.success("Авторизация", "Завершено успешно!");

      return authResponse;
    } catch (error) {
      toastError(error);

      return thunkAPI.rejectWithValue(error);
    }
  },
);

export const logout = createAsyncThunk("/logout", async () => {
  await AuthService.logout();
});

// export const checkAuth = createAsyncThunk<IAuthResponse>(
//   "auth/check-auth",
//   async (_, thunkAPI) => {
//     try {
//       const response = await AuthService.getNewTokens();

//       return response.data;
//     } catch (error) {
//       if (errorCatch(error) === "jwt expired") {
//         toastr.error(
//           "Выход",
//           "Ваша авторизация завершена, пожалуйста, войдите снова!",
//         );
//         thunkAPI.dispatch(logout());
//       }

//       return thunkAPI.rejectWithValue(error);
//     }
//   },
// );
