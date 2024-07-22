// Функция возвращает объект с заголовком, указывающим, что данные в формате JSON.
export const getContentType = () => ({
  "Content-Type": "application/json",
});

// Функция обрабатывает ошибку и возвращает сообщение об ошибке.
// Если ошибка содержит сообщение в формате объекта, возвращает первый элемент сообщения; иначе возвращает строку сообщения или общее сообщение об ошибке.
export const errorCatch = (error: any): string =>
  error.response && error.response.data
    ? typeof error.response.data.message === "object"
      ? error.response.data.message[0]
      : error.response.data.message
    : error.message;
