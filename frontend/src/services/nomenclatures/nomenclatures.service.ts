import axios from "axios";

import {
  NomenclatureInterface,
  NomenclatureListResponseInterface,
} from "@/src/types/interface/nomenclature.interface";
import { API_URL } from "@/src/config/api.config";
import { NomenclaturesPagination } from "@/src/types/interface/pagintaions.interface";

class NomenclaturesService {
  private URL = `${API_URL}/nomenclatures`;

  getAll(props: NomenclaturesPagination) {
    const params = new URLSearchParams();

    Object.entries(props).forEach(([key, value]) => {
      if (value !== undefined) {
        params.append(key, value.toString());
      }
    });

    const queryString = params.toString();
    const urlWithParams = `${this.URL}?${queryString}`;

    return axios.get<NomenclatureListResponseInterface>(urlWithParams);
  }

  getById(id: string | string[] | undefined) {
    return axios.get<NomenclatureInterface>(`${this.URL}/${id}`);
  }

  delete(id: string) {
    return axios.delete<NomenclatureInterface>(`${this.URL}/${id}`)
  }
}

export default new NomenclaturesService();
