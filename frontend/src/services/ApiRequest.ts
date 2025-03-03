// import { cookies } from "next/headers";
import axios, { AxiosError } from "axios";
import {getClientAccessToken, getServerAccessToken} from "@/utils";

interface ApiRequestParams {
    typeRequest: string;
    url: string;
    id?: string;
    queryParams?: any;
}



class ApiRequest implements ApiRequestParams {
    public typeRequest: string;
    public url: string;
    private token: string | null;

    constructor(typeRequest: string, url: string) {
        this.typeRequest = typeRequest;
        this.url = url;
        this.token = null;
    }

    private async ensureTokenInitialized() {
        if (!this.token) {
            if (typeof window === "undefined") {
                // Серверный код
                this.token = await getServerAccessToken();
            } else {
                // Клиентский код
                this.token = getClientAccessToken();
            }

            if (!this.token) {
                console.error("Токен не найден в куки");
                throw new Error("Вы не авторизованы");
            }
        }
    }


    public async getAuthHeader() {
        await this.ensureTokenInitialized();
        return {
            Authorization: `access_token ${this.token}`,
        };
    }

    private handleError(error: AxiosError) {
        let errorMessage = 'Произошла ошибка запроса';

        if (error.response) {
            // Если есть ответ от сервера, проверяем статус
            const status = error.response.status;
            // console.log(error.message, error.response?.status);

            if (status === 401) {
                errorMessage = "Необходима авторизация. Пожалуйста, войдите в систему.";
            } else if (status === 404) {
                errorMessage = "Запрашиваемые данные не найдены.";
            } else if (status === 500) {
                errorMessage = "Внутренняя ошибка сервера. Попробуйте позже.";
            } else {
                errorMessage = `Ошибка: ${status} - ${error.message}`;
            }
        } else if (error.request) {
            // Если запрос был отправлен, но ответа не было
            errorMessage = "Не удалось получить ответ от сервера.";
        } else {
            // Для других ошибок, например, проблемы с настройками запроса
            errorMessage = `Ошибка запроса: ${error.message}`;
        }

        return Promise.reject(new Error(errorMessage));
    }

    /**
     * Получение всего списка данных.
     *
     * @param queryParams - query параметры для запросов (поиск, пагинация и фильтрация)
     *
     * @example
     * ```typescript
     * class Example extends ApiRequest{
     *     constructor() {
     *         super('example', API_URL);
     *     }
     *
     *     async getAll(queryParams?: any): Promise<IExampleResponse> {
     *         return super.getAll(queryParams)
     *     }
     * }
     * ```
     * @param queryParams
     */
    async getAll(queryParams?: any) {
        try {
            const response = await axios.get(`${this.url}${this.typeRequest}/${queryParams}`, {
                headers: await this.getAuthHeader(),
                params: queryParams,
                method: 'no-cors',
            });

            if (response.status === 200) {
                return response.data;
            } else {
                return this.handleError(new Error(`Ошибка при запросе: ${response.status}`) as AxiosError);
            }
        } catch (error) {
            return this.handleError(error as AxiosError);
        }
    }

    async getById(id: string) {
        const response = await axios.get(`${this.url}${this.typeRequest}/${id}`, {
            headers: await this.getAuthHeader(),
        });

        if (response.status === 200) {
            return response.data;
        } else {
            return Promise.reject(new Error(`Ошибка при получении данных по ID ${id}: ${response.status}`));
        }
    }

    async deleteById(id: string) {
        const response = await axios.delete(`${this.url}${this.typeRequest}/${id}`, {
            headers: await this.getAuthHeader(),
        });

        if (response.status === 200) {
            return response.data;
        } else {
            return Promise.reject(new Error(`Ошибка при удалении элемента по ID ${id}: ${response.status}`));
        }
    }

    async updateById(id: string, data: any) {
        const response = await axios.put(`${this.url}${this.typeRequest}/${id}`, data, {
            headers: await this.getAuthHeader(),
        });

        if (response.status === 200) {
            return response.data;
        } else {
            return Promise.reject(new Error(`Ошибка при обновлении по ID ${id}: ${response.status}`));
        }
    }

}

export default ApiRequest;
