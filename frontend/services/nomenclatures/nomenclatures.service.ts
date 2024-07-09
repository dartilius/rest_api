import { API_URL } from "../../config/api.config";
import { NomenclatureListResponseInterface } from "../../types/interface/nomenclature.interface";
import { getTokenStorage } from "../auth/auth.helper";

interface Pagination {
  page?: number;
  limit?: number;
  search?: string;
  id?: string;
  versions?: string;
  status?: string;
  timezone?: string;
}

export const NomenclaturesService = {
  async getAll({
    page,
    limit,
    search,
    id,
    versions,
    status,
    timezone,
  }: Pagination = {}): Promise<NomenclatureListResponseInterface> {
    // Строим URL, учитывая, что `page` может быть undefined.
    let url = `${API_URL}/api/nomenclatures/`;

    const params = new URLSearchParams();

    if (page !== undefined) {
      params.append("page", page.toString());
    }
    if (limit !== undefined) {
      params.append("limit", limit.toString());
    }
    if (search !== undefined) {
      params.append("name", search);
    }
    if (id !== undefined) {
      params.append("id", id.toString());
    }
    if (versions !== undefined) {
      params.append("versions", versions.toString());
    }
    if (status !== undefined) {
      params.append("status", status.toString());
    }
    if (timezone !== undefined) {
      params.append("timezone", timezone.toString());
    }

    url += `?${params.toString()}`;

    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      return response.json();
    } else {
      throw new Error(`Не удалось получить список номенклатур`);
    }
  },

  async getById(id: string | string[]) {
    const response = await fetch(`${API_URL}/api/nomenclatures/${id}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      return response.json();
    } else {
      throw new Error("Не удалось получить номенклатуру");
    }
  },

  async create(updatedData: any) {
    const token = getTokenStorage();

    const response = await fetch(`${API_URL}/api/nomenclatures/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `access_token ${token}`,
      },
      body: JSON.stringify(updatedData),
    });

    if (response.status === 201 || response.status === 200) {
      return response;
    } else {
      throw new Error("Не удалось создать номенклатуру");
    }
  },

  async delete(id: string | string[] | undefined) {
    const token = getTokenStorage();

    const response = await fetch(`${API_URL}/api/nomenclatures/${id}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        Authorization: `access_token ${token}`,
      },
    });

    if (response.status === 204 || response.status === 200) {
      return response;
    } else {
      throw new Error("Не удалось удалить номенклатуру");
    }
  },

  async editById(
    id: string,
    data: { name: string; description: string; timezone: string },
  ) {
    const token = getTokenStorage();
    const response = await fetch(`${API_URL}/api/nomenclatures/${id}/`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `access_token ${token}`,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Не удалось отредактировать номенклатуру`);
    }
  },
};
