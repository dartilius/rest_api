import { toastr } from "react-redux-toastr";

export const toastSuccess = (success: any, title?: string) => {
  toastr.success(title || "Успешно", success);
  setTimeout(() => {
    toastr.clean()
  }, 3500)
};
