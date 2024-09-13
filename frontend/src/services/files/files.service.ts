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
  private URL = `${API_URL}/files/`;
  private token = getTokenStorage();

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

    return axios.get<FilesListResponse>(urlWithParams);
  }

  getById(id: string) {
    return axios.get<ReadFileResponse>(`${this.URL}${id}`);
  }

  create(data: any) {
    return axios.post(`${this.URL}`, data, {
      headers: {
        Authorization: `access_token ${this.token}`,
      }
    })
  }

  deleteById(id: string) {
    return axios.delete(`${this.URL}${id}`, {
      headers: {
        Authorization: `access_token ${this.token}`,
      }
    });
  }
}

export default new FilesService();
