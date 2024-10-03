//TODO: Переписать на классы

import axios from "axios";

import {
  FilesListResponse,
  ReadFileResponse,
} from "@/src/types/interface/files.interface";
import { API_URL } from "@/src/config/api.config";
import {getTokenStorage} from "@/src/services/auth/auth.helper";

interface Pagination {
  page?: number;
  limit?: number;
  name?: string;
  file_type?: string;
  tags?: string[];
  hash?: string;
}

class FilesService {
  private token = getTokenStorage();
  private URL = `${API_URL}/files/`;

  getAll(props: Pagination) {
    const params = new URLSearchParams();

    if (props.page !== undefined) {
      params.append("page", props.page.toString());
    }
    if (props.limit !== undefined) {
      params.append("limit", props.limit.toString());
    }
    if (props.name !== undefined) {
      params.append("name", props.name);
    }
    if (props.file_type !== undefined) {
      params.append("file_type", props.file_type);
    }
    if (props.tags !== undefined) {
      params.append("tags", props.tags.toString());
    }
    if (props.hash !== undefined) {
      params.append("hash", props.hash);
    }

    const queryString = params.toString();
    const urlWithParams = `${this.URL}?${queryString}`;

    return axios.get<FilesListResponse>(urlWithParams, {
      headers: {
        Authorization: `access_token ${this.token}`,
      },
    });
  }

  getById(id: string) {
    return axios.get<ReadFileResponse>(`${this.URL}${id}`, {
      headers: {
        Authorization: `access_token ${this.token}`,
      },
    });
  }
}

export default new FilesService();

// export const FilesService = {
//   async getAll({
//     page,
//     limit,
//     name,
//     file_type,
//     tags,
//     hash,
//   }: Pagination = {}): Promise<FilesListResponse> {
//     const params = new URLSearchParams();

//     if (page !== undefined) {
//       params.append("page", page.toString());
//     }
//     if (limit !== undefined) {
//       params.append("limit", limit.toString());
//     }
//     if (name !== undefined) {
//       params.append("name", name);
//     }
//     if (file_type !== undefined) {
//       params.append("file_type", file_type);
//     }
//     if (tags !== undefined) {
//       tags.forEach((tag) => params.append("tags", tag));
//     }
//     if (hash !== undefined) {
//       params.append("hash", hash);
//     }

//     const url = `${API_URL}/api/files/?${params.toString()}`;

//     const response = await fetch(url, {
//       method: "GET",
//       headers: {
//         "Content-Type": "application/json",
//       },
//     });

//     if (response.ok) {
//       const data: FilesListResponseDTO = await response.json();

//       return filesListResponseTransformer(data);
//     } else {
//       throw new Error("Не удалось получить список файлов");
//     }
//   },

//   async createFiles(
//     fileData: { file_type: number; source: string; tags: number[] },
//     token: string | null,
//   ): Promise<FilesCreateResponse> {
//     const url = `${API_URL}/api/files/`;

//     const payload = {
//       ...fileData,
//       file_type: Number(fileData.file_type),
//     };

//     try {
//       const response = await fetch(url, {
//         method: "POST",
//         headers: {
//           "Content-Type": "application/json",
//           Authorization: `access_token ${token}`,
//         },
//         body: JSON.stringify(payload),
//       });

//       if (response.ok) {
//         const data = await response.json();

//         // toastSuccess("Файл успешно создан");

//         return filesCreateResponseTransformer(data);
//       } else {
//         const errorData = await response.json();

//         throw new Error(
//           `Не удалось создать файл: ${errorData.detail || response.statusText}`,
//         );
//       }
//     } catch (error) {
//       // toastError(error);
//       throw error;
//     }
//   },

//   async createTags(
//     tagsData: TagsCreateRequest,
//     token: string | null,
//   ): Promise<TagsCreateResponse> {
//     const url = `${API_URL}/api/tags/`;
//     const body = JSON.stringify(tagsData);

//     try {
//       const response = await fetch(url, {
//         method: "POST",
//         headers: {
//           "Content-Type": "application/json",
//           Authorization: `access_token ${token}`,
//         },
//         body: body,
//       });

//       if (response.ok) {
//         const data: TagsCreateResponse = await response.json();

//         // toastSuccess("Тег успешно создан");

//         return data;
//       } else {
//         throw new Error(`${(response.status, response.statusText)}`);
//       }
//     } catch (error) {
//       // toastError(error);
//       throw error;
//     }
//   },

//   async getById(id: string | string[] | undefined): Promise<ReadFileResponse> {
//     const url = `${API_URL}/api/files/${id}`;

//     const token = getTokenStorage();

//     try {
//       const response = await fetch(url, {
//         method: "GET",
//         headers: {
//           "Content-Type": "application/json",
//           Authorization: `access_token ${token}`,
//         },
//       });

//       if (response.ok) {
//         const data: ReadFileResponseDTO = await response.json();

//         return readFileResponseTransformer(data);
//       } else {
//         throw new Error(`Не удалось получить файл: ${response.statusText}`);
//       }
//     } catch (error) {
//       throw error;
//     }
//   },

//   async update(
//     id: string,
//     data: UpdateFileRequest,
//     token: string | undefined,
//   ): Promise<any> {
//     const url = `${API_URL}/api/files/${id}`;
//     const body = JSON.stringify(data);

//     try {
//       const response = await fetch(url, {
//         method: "PUT",
//         headers: {
//           "Content-Type": "application/json",
//           Authorization: `access_token ${token}`,
//         },
//         body: body,
//       });

//       if (response.ok) {
//         // toastSuccess("Файл успешно обновлен");
//       } else {
//         throw new Error(`Не удалось обновить файл: ${response.statusText}`);
//       }
//     } catch (error) {
//       // toastError(error);
//       throw error;
//     }
//   },
// };
