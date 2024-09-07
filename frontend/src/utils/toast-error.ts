import { toastr } from "react-redux-toastr";

export const toastError = (error: any, title?: string) => {
  toastr.error(title || "Ошибка запроса", error);
};
