//TODO: Переписать на классы

import { API_URL } from "@/src/config/api.config";
import {
  AdOrdersListResponse,
  AdOrdersListResponseDTO,
  BgOrdersListResponse,
  BgOrdersListResponseDTO,
} from "@/src/types/interface/orders.interface";
import {
  AdOrderResponseTransformer,
  BgOrderResponseTransformer,
} from "@/src/types/transformers/orders.transformer";

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

export const AdOrdersService = {
  async getAll(params: AdOrdersQueryParams): Promise<AdOrdersListResponse> {
    const { page, limit, group, brc_type, owner, created, id, name } = params;
    let url = `${API_URL}/api/adorders/`;

    if (page !== undefined) {
      url += `?page=${page}`;
    }
    if (limit !== undefined) {
      url += `&limit=${limit}`;
    }
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      const data: AdOrdersListResponseDTO = await response.json();

      return AdOrderResponseTransformer(data);
    } else {
      throw new Error("Не удалось получить список заявок");
    }
  },
};

export const BgOrdersService = {
  async getAll(params: BgOrdersQueryParams): Promise<BgOrdersListResponse> {
    const { page, limit, client, created, id, name, order_type, owner } =
      params;
    let url = `${API_URL}/api/bgorders/`;

    if (page !== undefined) {
      url += `?page=${page}`;
    }
    if (limit !== undefined) {
      url += `&limit=${limit}`;
    }
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      const data: BgOrdersListResponseDTO = await response.json();

      return BgOrderResponseTransformer(data);
    } else {
      throw new Error("Не удалось получить список заявок");
    }
  },
};
