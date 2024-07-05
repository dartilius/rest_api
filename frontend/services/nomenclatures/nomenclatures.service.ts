import { API_URL } from "../../config/api.config";
import { NomenclatureListResponseInterface } from "../../types/interface/nomenclature.interface";

interface Pagination {
  page?: number;
  limit?: number;
  search?: string;
  id?: string;
  version?: string;
  status?: string;
}

export const NomenclaturesService = {
  async getAll({
    page,
    limit,
    search,
    id,
    version,
    status,
  }: Pagination = {}): Promise<NomenclatureListResponseInterface> {
    // Строим URL, учитывая, что `page` может быть undefined.
    let url = `${API_URL}/api/nomenclatures/`;

    if (page !== undefined) {
      url += `?page=${page}`;
    }
    if (limit !== undefined) {
      url += `&limit=${limit}`;
    }
    if (search !== undefined) {
      url += `&name=${search}`;
    }
    if (id !== undefined) {
      url += `&id=${id}`;
    }
    if (version !== undefined) {
      url += `&version=${version}`;
    }
    if (status !== undefined) {
      url += `&version=${status}`;
    }

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
    console.log(id);

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

  async create(updatedData: any, token: string | undefined) {
    const response = await fetch(`${API_URL}/api/nomenclatures/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(updatedData),
    });

    if (response.status === 201 || response.status === 200) {
      return response;
    } else {
      throw new Error("Не удалось создать номенклатуру");
    }
  },

  async delete(token: string | undefined, id: string | string[] | undefined) {
    const response = await fetch(`${API_URL}/api/nomenclatures/${id}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });

    if (response.status === 204 || response.status === 200) {
      return response;
    } else {
      throw new Error("Не удалось удалить номенклатуру");
    }
  },
};
