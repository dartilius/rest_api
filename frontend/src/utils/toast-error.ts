import { toastr } from "react-redux-toastr";

import { errorCatch } from "@/src/api/api.helpers";

export const toastError = (error: any, title?: string) => {
  const message = errorCatch(error);

  toastr.error(title || "Ошибка", message);
};
