import { API_URL } from "@/config/api.config";
import {
  INomenclatureByIdResponse,
  INomenclaturesResponse,
  INomenclaturesService,
} from "@/interfaces/Nomenclatures.interface";
import axios from "axios";

class NomenclaturesService {
  private URL = API_URL;
  constructor() {}

  getAll({ limit, page, token }: INomenclaturesService) {
    return axios.get<INomenclaturesResponse>(
      `${this.URL}nomenclatures/?page=${page}&limit=${limit}`,
      {
        headers: {
          Authorization: `access_token ${token}`,
        },
      }
    );
  }

  getById({ id, token }: { id: string | undefined; token: string | null }) {
    return axios.get<INomenclatureByIdResponse>(
      `${this.URL}nomenclatures/${id}`,
      {
        headers: {
          Authorization: `access_token ${token}`,
        },
      }
    );
  }
}

export default new NomenclaturesService();
