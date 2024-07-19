import axios from "axios";

import {
  NomenclatureListInterface,
  NomenclatureListResponseInterface,
} from "@/src/types/interface/nomenclature.interface";
import { API_URL } from "@/src/config/api.config";

interface Pagination {
  page?: number;
  limit?: number;
  search?: string;
  id?: string;
  versions?: string;
  status?: string;
  timezone?: string;
}

export interface ITodo {
  id: number;
  title: string;
  completed: boolean;
  userId: number;
}

class NomenclaturesService {
  private URL = `${API_URL}/nomenclatures`;

  getAll(props: Pagination = {}) {
    const params = new URLSearchParams();

    if (props.page !== undefined) {
      params.append("page", props.page.toString());
    }
    if (props.limit !== undefined) {
      params.append("limit", props.limit.toString());
    }
    if (props.search !== undefined) {
      params.append("search", props.search);
    }
    if (props.id !== undefined) {
      params.append("id", props.id);
    }
    if (props.versions !== undefined) {
      params.append("versions", props.versions);
    }
    if (props.status !== undefined) {
      params.append("status", props.status);
    }
    if (props.timezone !== undefined) {
      params.append("timezone", props.timezone);
    }

    const queryString = params.toString();
    const urlWithParams = `${this.URL}?${queryString}`;

    return axios.get<NomenclatureListResponseInterface>(urlWithParams);
  }

  getById(id: string) {
    return axios.get<NomenclatureListInterface>(`${this.URL}/${id}`);
  }
}

export default new NomenclaturesService();
