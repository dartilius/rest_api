import { API_URL } from "@/config/api.config";
import {
  INomenclatureByIdResponse,
  INomenclaturesResponse,
  INomenclaturesService,
} from "@/interfaces/Nomenclatures.interface";
import axios from "axios";
import { getAccessToken } from "./accessToken";
import { IVersions } from "@/hooks/useFetchNomenclatures";
import ApiRequest from "@/services/ApiRequest";

class NomenclaturesService extends ApiRequest{
  private URL = API_URL;
  private TOKEN = getAccessToken();
  constructor() {
    super('nomenclatures', API_URL);
  }

  async getAll({page, limit}: INomenclaturesService): Promise<INomenclaturesResponse> {
    const newQueryParams = `?page=${page}&limit=${limit}`;
    return super.getAll(newQueryParams);
  }

  // async getAll({
  //   limit,
  //   page,
  //   search,
  //   status,
  //   timezone,
  //   version,
  // }: INomenclaturesService) {
  //   return axios.get<INomenclaturesResponse>(
  //     `${this.URL}nomenclatures/?page=${page}&limit=${limit}&name=${search}&status=${status}&timezone=${timezone}&version=${version}`,
  //     {
  //       headers: {
  //         Authorization: `access_token ${this.TOKEN}`,
  //       },
  //     }
  //   );
  // }

  async getById(id: string | undefined) {
    return axios.get<INomenclatureByIdResponse>(
      `${this.URL}nomenclatures/${id}`,
      {
        headers: {
          Authorization: `access_token ${this.TOKEN}`,
        },
      }
    );
  }

  async getVersions() {
    return axios.get<IVersions>(`${this.URL}nomenclatures/versions/`, {
      headers: {
        Authorization: `access_token ${this.TOKEN}`,
      },
    });
  }
}

export default new NomenclaturesService();
