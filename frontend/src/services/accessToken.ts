const key = "accessToken";

export function getAccessToken(): string | null {
  // Проверяем доступность localStorage (только на клиентской стороне)
  if (typeof window === "undefined") {
    return null;
  }

  try {
    return window.localStorage.getItem(key);
  } catch (error) {
    console.error("Error accessing localStorage:", error);
    return null;
  }
}
