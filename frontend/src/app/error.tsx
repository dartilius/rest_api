"use client";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ErrorPage({ error, reset }: ErrorProps) {
  // Получаем статус код из сообщения об ошибке
  const statusCode = error.message.match(/Error: (\d+)/)?.[1] || "500";
  
  // Описания для разных ошибок
  const errorMessages: Record<string, string> = {
    "401": "Требуется авторизация",
    "403": "Доступ запрещён",
    "404": "Страница не найдена",
    "500": "Ошибка сервера",
    "502": "Проблемы с соединением",
  };

  return (
    <div className="error-container">
      <h1>Ошибка {statusCode}</h1>
      <p>{errorMessages[statusCode] || "Неизвестная ошибка"}</p>
      <button onClick={reset}>Попробовать снова</button>
    </div>
  );
}