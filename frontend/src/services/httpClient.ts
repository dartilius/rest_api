class HttpError extends Error {
    status: number;
    url: string;
  
    constructor(message: string, status: number, url: string) {
      super(message);
      this.status = status;
      this.url = url;
      this.name = 'HttpError';
    }
  }
  
  class HttpClient {
    async request<T>(
      method: string,
      url: string,
      options?: { body?: any; params?: { [key: string]: any }; headers?: { [key: string]: string } }
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
        throw new HttpError(errorMessage, response.status, urlWithParams);
      }
  
      return (await response.json()) as T;
    }
  
    get<T>(url: string, options?: { params?: { [param: string]: any }; headers?: { [key: string]: string } }) {
      return this.request<T>("GET", url, options);
    }
  
    post<T>(url: string, options?: { body?: any; headers?: { [key: string]: string } }) {
      return this.request<T>("POST", url, options);
    }
  
    put<T>(url: string, options?: { body?: any; headers?: { [key: string]: string } }) {
      return this.request<T>("PUT", url, options);
    }
  
    delete<T>(url: string, options?: { params?: { [param: string]: any }; headers?: { [key: string]: string } }) {
      return this.request<T>("DELETE", url, options);
    }
  }
  
  export const client = new HttpClient();
  