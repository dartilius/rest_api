export const getContentType = () => ({
  "Content-Type": "application/json",
});

export const errorCatch = (error: any): string => {
  if (error.response && error.response.data) {
    if (typeof error.response.data === "object") {
      return Object.values(error.response.data).flat().join(", ");
    } else {
      return (
        error.response.data.message || error.message || "Неизвестная ошибка"
      );
    }
  } else {
    return error.message || "Неизвестная ошибка";
  }
};
export const handleResponse = (response: any): string => {
  if (response && response.status >= 200 && response.status < 300) {
    return response.data && response.data.message
      ? response.data.message
      : "Успешный ответ без сообщения";
  } else {
    return errorCatch({ response });
  }
};
