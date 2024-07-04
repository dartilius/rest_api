import { toastr } from "react-redux-toastr";

import { handleResponse } from "../api/api.helpers";

export const toastSuccess = (success: any, title?: string) => {
  const message =
    typeof success === "string" ? success : handleResponse(success);

  toastr.success(title || "Успешно", message);
};
