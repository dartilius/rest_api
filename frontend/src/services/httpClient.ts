// import {redirect} from "next/navigation";

// class HttpError extends Error {
//     status: number;
//     url: string;
  
//     constructor(message: string, status: number, url: string) {
//       super(message);
//       this.status = status;
//       this.url = url;
//       this.name = 'HttpError';
//     }
//   }
  
//   export class HttpClient {
//     async request<T>(
//       method: string,
//       url: string,
//       options?: { body?: any; params?: { [key: string]: any }; headers?: { [key: string]: string } }
//     ): Promise<T> {
//       let urlWithParams = url;
  
//       if (options?.params) {
//         urlWithParams += `?${new URLSearchParams(options.params).toString()}`;
//       }
  
//       const response = await fetch(urlWithParams, {
//         method,
//         credentials: "include",
//         headers: {
//           "Content-Type": "application/json",
//           ...(options?.headers || {}),
//         },
//         body: options?.body ? JSON.stringify(options.body) : undefined,
//       });

//       if (response.status === 401) {
//         redirect('login')
//       }
  
//       if (!response.ok) {
//         const errorMessage = `Error: ${response.status} - ${response.statusText}`;
//         throw new HttpError(errorMessage, response.status, urlWithParams);
//       }

//       if (response.status === 204) {
//         return response.status as unknown as T;
//       }
  
//       return (await response.json()) as T;
//     }
  
//     get<T>(url: string, options?: { params?: { [param: string]: any }; headers?: { [key: string]: string } }) {
//       return this.request<T>("GET", url, options);
//     }
  
//     post<T>(url: string, options?: { body?: any; headers?: { [key: string]: string } }) {
//       return this.request<T>("POST", url, options);
//     }
  
//     put<T>(url: string, options?: { body?: any; headers?: { [key: string]: string } }) {
//       return this.request<T>("PUT", url, options);
//     }
  
//     delete<T>(url: string, options?: { params?: { [param: string]: any }; headers?: { [key: string]: string } }) {
//       return this.request<T>("DELETE", url, options);
//     }
//   }
  
//   export const client = new HttpClient();
import { redirect } from "next/navigation";

class HttpError extends Error {
  status: number;
  url: string;
  response: Response;

  constructor(
    message: string,
    status: number,
    url: string,
    response: Response
  ) {
    super(message);
    this.status = status;
    this.url = url;
    this.response = response;
    this.name = "HttpError";
  }
}

type ErrorHandler = (error: HttpError) => void;

interface RequestOptions {
  body?: any;
  params?: { [key: string]: any };
  headers?: { [key: string]: string };
  errorHandlers?: Record<number, ErrorHandler>;
}

export class HttpClient {
  private errorHandlers: Map<number, ErrorHandler> = new Map();

  registerErrorHandler(status: number, handler: ErrorHandler) {
    this.errorHandlers.set(status, handler);
  }

  async request<T>(
    method: string,
    url: string,
    options?: RequestOptions
  ): Promise<T> {
    let urlWithParams = url;

    if (options?.params) {
      urlWithParams += `?${new URLSearchParams(options.params).toString()}`;
    }

    const response = await fetch(urlWithParams, {
      method,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
      body: options?.body ? JSON.stringify(options.body) : undefined,
    });

    if (!response.ok) {
      const errorMessage = `Error: ${response.status} - ${response.statusText}`;
      const error = new HttpError(
        errorMessage,
        response.status,
        urlWithParams,
        response
      );

      // Сначала проверяем локальные обработчики
      const localHandler = options?.errorHandlers?.[response.status];
      if (localHandler) {
        localHandler(error);
      }
      // Затем глобальные обработчики
      else {
        const globalHandler = this.errorHandlers.get(response.status);
        if (globalHandler) {
          globalHandler(error);
        }
      }

      throw error;
    }

    if (response.status === 204) {
      return response.status as unknown as T;
    }

    return (await response.json()) as T;
  }

  get<T>(url: string, options?: Omit<RequestOptions, "body">) {
    return this.request<T>("GET", url, options);
  }

  post<T>(url: string, options?: Omit<RequestOptions, "params">) {
    return this.request<T>("POST", url, options);
  }

  put<T>(url: string, options?: Omit<RequestOptions, "params">) {
    return this.request<T>("PUT", url, options);
  }

  delete<T>(url: string, options?: Omit<RequestOptions, "body">) {
    return this.request<T>("DELETE", url, options);
  }
}

export const client = new HttpClient();

// Пример регистрации обработчиков по умолчанию
// Глобальная обработка 500 ошибки
client.registerErrorHandler(401, () => redirect("/login"));


// Запрос с кастомным обработчиком
// client.get("/api/data", {
//   errorHandlers: {
//     403: () => redirect("/custom-forbidden"),
//     404: (error) => {
//       console.warn("Not found:", error.url);
//       redirect("/custom-not-found");
//     }
//   }
// });