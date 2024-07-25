import axios from "axios";

import { API_URL } from "@/src/config/api.config";
import {
  AdOrdersListResponse,
  BgOrdersListResponse,
} from "@/src/types/interface/orders.interface";

interface BgOrdersQueryParams {
  name?: string;
  id?: string;
  client?: string;
  order_type?: string;
  owner?: string;
  created?: string;
  page: number;
  limit: number;
}

interface AdOrdersQueryParams {
  name?: string;
  id?: string;
  group?: string;
  brc_type?: string;
  owner?: string;
  created?: string;
  page: number;
  limit: number;
}

class OrdersService {
  private URL: string = `${API_URL}`;

  advertising() {
    const advertisingUrl = this.URL + "/bgorders/";

    return {
      gatAll(props: BgOrdersQueryParams) {
        const params = new URLSearchParams();

        if (props.page !== undefined) {
          params.append("page", props.page.toString());
        }
        if (props.limit !== undefined) {
          params.append("limit", props.limit.toString());
        }

        const queryString = params.toString();
        const urlWithParams = `${advertisingUrl}?${queryString}`;

        return axios.get<AdOrdersListResponse>(urlWithParams);
      },
    };
  }

  background() {
    const backgroundUrl = this.URL + "/bgorders/";

    return {
      gatAll(props: AdOrdersQueryParams) {
        const params = new URLSearchParams();

        if (props.page !== undefined) {
          params.append("page", props.page.toString());
        }
        if (props.limit !== undefined) {
          params.append("limit", props.limit.toString());
        }

        const queryString = params.toString();
        const urlWithParams = `${backgroundUrl}?${queryString}`;

        return axios.get<BgOrdersListResponse>(urlWithParams);
      },
    };
  }
}

export default new OrdersService();
