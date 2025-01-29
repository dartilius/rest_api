import { API_URL } from "@/config/api.config";
import {
  INomenclatureByIdResponse,
  INomenclaturesResponse,
  INomenclaturesService,
} from "@/interfaces/Nomenclatures.interface";
import axios from "axios";
import { getAccessToken } from "./accessToken";

class NomenclaturesService {
  private URL = API_URL;
  private TOKEN = getAccessToken();
  constructor() {}

  getAll({ limit, page }: INomenclaturesService) {
    return axios.get<INomenclaturesResponse>(
      `${this.URL}nomenclatures/?page=${page}&limit=${limit}`,
      {
        headers: {
          Authorization: `access_token ${this.TOKEN}`,
        },
      }
    );
  }

  getById(id: string | undefined) {
    return axios.get<INomenclatureByIdResponse>(
      `${this.URL}nomenclatures/${id}`,
      {
        headers: {
          Authorization: `access_token ${this.TOKEN}`,
        },
      }
    );
  }
}

export default new NomenclaturesService();
