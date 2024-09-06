import axios from "axios";

import { API_URL } from "@/src/config/api.config";
import { GroupsListResponse } from "@/src/types/interface/groups.interface";

interface Pagination {
  page?: number;
  limit?: number;
}

class GroupsService {
  private URL = `${API_URL}/groups`;

  getAll(props: Pagination = {}) {
    const params = new URLSearchParams();

    if (props.page !== undefined) {
      params.append("page", props.page.toString());
    }
    if (props.limit !== undefined) {
      params.append("limit", props.limit.toString());
    }

    const queryString = params.toString();
    const urlWithParams = `${this.URL}?${queryString}`;

    return axios.get<GroupsListResponse>(urlWithParams);
  }
}

export default new GroupsService();
