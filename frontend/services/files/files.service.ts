import { API_URL } from "../../config/api.config";
import {
  FilesCreateResponse,
  FilesListResponse,
  FilesListResponseDTO,
  ReadFileResponse,
  ReadFileResponseDTO,
  TagsCreateRequest,
  TagsCreateResponse,
  UpdateFileRequest,
} from "../../types/interface/files.interface";
import {
  filesCreateResponseTransformer,
  filesListResponseTransformer,
  readFileResponseTransformer,
} from "../../types/transformers/files.transformer";
import { getTokenStorage } from "../auth/auth.helper";
interface Pagination {
  page?: number;
  limit?: number;
  name?: string;
  file_type?: string;
}

const fetchWithTimeout = async (
  url: RequestInfo | URL,
  options: RequestInit | undefined,
  timeout = 5000,
) => {
  return Promise.race([
    fetch(url, options),
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error("Request timed out")), timeout),
    ),
  ]) as unknown as Response;
};

export const FilesService = {
  async getAll({
    page,
    limit,
    name,
    file_type,
  }: Pagination = {}): Promise<FilesListResponse> {
    let url = `${API_URL}/api/files/`;

    if (page !== undefined) {
      url += `?page=${page}`;
    }
    if (limit !== undefined) {
      url += `&limit=${limit}`;
    }
    if (name !== undefined) {
      url += `&name=${name}`;
    }
    if (file_type !== undefined) {
      url += `&file_type=${file_type}`;
    }

    const response = await fetchWithTimeout(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      const data: FilesListResponseDTO = await response.json();

      return filesListResponseTransformer(data);
    } else {
      throw new Error("Не удалось получить список файлов");
    }
  },

  async createFiles(
    fileData: { file_type: number; source: string; tags: number[] },
    token: string | null,
  ): Promise<FilesCreateResponse> {
    const url = `${API_URL}/api/files/`;

    const payload = {
      ...fileData,
      file_type: Number(fileData.file_type),
    };

    try {
      const response = await fetchWithTimeout(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `access_token ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const data = await response.json();

        // toastSuccess("Файл успешно создан");

        return filesCreateResponseTransformer(data);
      } else {
        const errorData = await response.json();

        throw new Error(
          `Не удалось создать файл: ${errorData.detail || response.statusText}`,
        );
      }
    } catch (error) {
      // toastError(error);
      throw error;
    }
  },

  async createTags(
    tagsData: TagsCreateRequest,
    token: string | null,
  ): Promise<TagsCreateResponse> {
    const url = `${API_URL}/api/tags/`;
    const body = JSON.stringify(tagsData);

    try {
      const response = await fetchWithTimeout(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `access_token ${token}`,
        },
        body: body,
      });

      if (response.ok) {
        const data: TagsCreateResponse = await response.json();

        // toastSuccess("Тег успешно создан");

        return data;
      } else {
        throw new Error(`${(response.status, response.statusText)}`);
      }
    } catch (error) {
      // toastError(error);
      throw error;
    }
  },

  async getById(id: string | string[] | undefined): Promise<ReadFileResponse> {
    const url = `${API_URL}/api/files/${id}`;

    const token = getTokenStorage();

    try {
      const response = await fetchWithTimeout(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `access_token ${token}`,
        },
      });

      if (response.ok) {
        const data: ReadFileResponseDTO = await response.json();

        return readFileResponseTransformer(data);
      } else {
        throw new Error(`Не удалось получить файл: ${response.statusText}`);
      }
    } catch (error) {
      throw error;
    }
  },

  async update(
    id: string,
    data: UpdateFileRequest,
    token: string | undefined,
  ): Promise<any> {
    const url = `${API_URL}/api/files/${id}`;
    const body = JSON.stringify(data);

    try {
      const response = await fetchWithTimeout(url, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `access_token ${token}`,
        },
        body: body,
      });

      if (response.ok) {
        // toastSuccess("Файл успешно обновлен");
      } else {
        throw new Error(`Не удалось обновить файл: ${response.statusText}`);
      }
    } catch (error) {
      // toastError(error);
      throw error;
    }
  },
};
