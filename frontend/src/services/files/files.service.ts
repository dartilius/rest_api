import axios from "axios";

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

  create(data: FilesCreateRequest) {
    return axios.post<FilesCreateRequest>(`${this.URL}`, data, {
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

    return axios.get<ITagsList>(urlWithParams, {
      headers: {
        Authorization: `access_token ${this.token}`,
      }
    })
  }

  updateById(id: string, data: any) {
    return axios.patch(`${this.URL}${id}/`, data, {
      headers: {
        Authorization: `access_token ${this.token}`,
      },
    })
  }

  deleteById(id: string) {
    return axios.delete(`${this.URL}${id}/`, {
      headers: {
        Authorization: `access_token ${this.token}`,
      },
    });
  }
}

export default new FilesService();