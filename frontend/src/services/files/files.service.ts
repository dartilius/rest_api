//TODO: Переписать на классы

import { getTokenStorage } from "../auth/auth.helper";

import {
  FilesCreateResponse,
  FilesListResponse,
  FilesListResponseDTO,
  ReadFileResponse,
  ReadFileResponseDTO,
  TagsCreateRequest,
  TagsCreateResponse,
  UpdateFileRequest,
} from "@/src/types/interface/files.interface";
import { API_URL } from "@/src/config/api.config";
import {
  filesCreateResponseTransformer,
  filesListResponseTransformer,
  readFileResponseTransformer,
} from "@/src/types/transformers/files.transformer";

interface Pagination {
  page?: number;
  limit?: number;
  name?: string;
  file_type?: string;
  tags?: string[];
  hash?: string;
}

export const FilesService = {
  async getAll({
    page,
    limit,
    name,
    file_type,
    tags,
    hash,
  }: Pagination = {}): Promise<FilesListResponse> {
    const params = new URLSearchParams();

    if (page !== undefined) {
      params.append("page", page.toString());
    }
    if (limit !== undefined) {
      params.append("limit", limit.toString());
    }
    if (name !== undefined) {
      params.append("name", name);
    }
    if (file_type !== undefined) {
      params.append("file_type", file_type);
    }
    if (tags !== undefined) {
      tags.forEach((tag) => params.append("tags", tag));
    }
    if (hash !== undefined) {
      params.append("hash", hash);
    }

    const url = `${API_URL}/api/files/?${params.toString()}`;

    const response = await fetch(url, {
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
      const response = await fetch(url, {
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
      const response = await fetch(url, {
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
      const response = await fetch(url, {
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
      const response = await fetch(url, {
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
