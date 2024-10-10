import axios, {AxiosInstance} from "axios";

import {
  FilesCreateRequest,
  FilesListResponse, ITagsList,
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
  private TAGS = `${API_URL}/tags/`
  private axiosInstance: AxiosInstance;

  constructor() {
    this.axiosInstance = axios.create({
      headers: {
        'Content-Type': 'application/json',
        Authorization: `access_token ${this.token}`,
      },
    });

    // Set up an interceptor to handle 401 errors
    this.axiosInstance.interceptors.response.use(
        (response) => response,
        (error) => {
          // Ensure the code is executed only on the client side
          if (typeof window !== 'undefined' && error.response && error.response.status === 401) {
            window.location.href = '/login';
          }
          return Promise.reject(error);
        }
    );

  }


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
    if (props.tags && props.tags.length > 0) {
      params.append("tags", props.tags.toString());
    }
    if (props.hash !== undefined) {
      params.append("hash", props.hash);
    }

    const queryString = params.toString();
    const urlWithParams = `${this.URL}?${queryString}`;

    return this.axiosInstance.get<FilesListResponse>(urlWithParams, {
      headers: {
        Authorization: `access_token ${this.token}`,
      },
    });
  }

  getById(id: string) {
    return this.axiosInstance.get<ReadFileResponse>(`${this.URL}${id}`, {
      headers: {
        Authorization: `access_token ${this.token}`,
      },
    });
  }

  create(data: FilesCreateRequest) {
    return this.axiosInstance.post<FilesCreateRequest>(`${this.URL}`, data, {
      headers: {
        Authorization: `access_token ${this.token}`,
      },
    })
  }

  getALlTags(props: Pagination) {
    const params = new URLSearchParams();
    const {page, limit} = props;

    if (page !== undefined) {
      params.append("page", page.toString());
    }
    if (limit !== undefined) {
      params.append("limit", limit.toString());
    }

    const queryString = params.toString();
    const urlWithParams = `${this.TAGS}?${queryString}`;

    return this.axiosInstance.get<ITagsList>(urlWithParams, {
      headers: {
        Authorization: `access_token ${this.token}`,
      }
    })
  }

  updateById(id: string, data: any) {
    return this.axiosInstance.patch(`${this.URL}${id}/`, data, {
      headers: {
        Authorization: `access_token ${this.token}`,
      },
    })
  }

  deleteById(id: string) {
    return this.axiosInstance.delete(`${this.URL}${id}/`, {
      headers: {
        Authorization: `access_token ${this.token}`,
      },
    });
  }
}

export default new FilesService();