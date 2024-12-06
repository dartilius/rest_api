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

  getAll({ limit, page, token, timezone, status }: INomenclaturesService) {
    return axios.get<INomenclaturesResponse>(
      `${this.URL}nomenclatures/?page=${page}&limit=${limit}&timezone=${timezone}&status=${status}`,
      {
        headers: {
          Authorization: `access_token ${token}`,
        },
      }
    );
  }

  getById({ id, token }: { id: string; token: string }) {
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
