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
import {getServerAccessToken} from "@/utils";

export class NomenclaturesService extends ApiRequest{
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

type fetchNomenclaturesQuery = {
  page?: number | string;
  limit?: number | string;
  name?: string;
  status?: string;
  timezone?: string;
  version?: string;
}

export type NomenclaturesDataList = {
  id: string;
  article: string;
  name: string;
  timezone: string;
  status: string;
  last_answer: string;
  version: string;
}

export type fetchNomenclaturesResponse = {
  count: number;
  next: string;
  previous: string;
  results: NomenclaturesDataList[];
}

const defaultHeaders = {
  'Accept': 'application/json',
  'Content-Type': 'application/json',
}

export default async function fetchNomenclatures(props: fetchNomenclaturesQuery): Promise<fetchNomenclaturesResponse> {
  const { name, page, limit, version, status, timezone } = props;
  const token = await getServerAccessToken()
  try {
    const response = await fetch(`${API_URL}/nomenclatures/?page=${page}&limit=${limit}&name=${name}&version=${version}&status=${status}&timezone=${timezone}`, {
      headers: {
        ...defaultHeaders,
        'Authorization': `access_token ${token}`,
      }
    });

    if (!response.ok) {
      throw new Error('No such nomenclature');
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching nomenclatures:', error);
    throw new Error('Failed to fetch nomenclatures');
  }
}

export async function deleteNomenclatures(id: string) {
  const token = await getServerAccessToken()
  try {
    const response = await fetch(`${API_URL}/nomenclatures/${id}/`, {
      method: 'DELETE',
      headers: {
        ...defaultHeaders,
        'Authorization': `access_token ${token}`,
      }
    });

    if (!response.ok) {
      throw new Error('No id nomenclature');
    }

    return response.status;
  } catch (error) {
    console.error('Error delete nomenclatures:', error);
    throw new Error('Failed delete nomenclatures');
  }
}
export async function resendOrders(id: string) {
  const token = await getServerAccessToken();
  try {
    const resend = await fetch(`${API_URL}/nomenclatures/${id}/resend_orders/`, {
      headers: {
        ...defaultHeaders,
        Authorization: `access_token ${token}`,
      },
      method: 'POST',
    });

    const responseBody = await resend.json();

    return {
      status: resend.status,
      message: responseBody.message || `Статус: ${resend.status}`,
      detail: responseBody.detail,
    };
  } catch (error) {
    console.error('Ошибка при переотправке заказов:', error);
    throw error;
  }
}

export async function sendActions(id: string, type: string) {
  const token = await getServerAccessToken();

  try {
    const resend = await fetch(`${API_URL}/nomenclatures/${id}/actions/`, {
      headers: {
        ...defaultHeaders,
        Authorization: `access_token ${token}`,
      },
      method: 'POST',
      body: JSON.stringify({"task": type}),
    });

    const responseBody = await resend.json();

    return {
      status: resend.status,
      message: responseBody.message || `Статус: ${resend.status}`,
      detail: responseBody.detail,
    };
  } catch (error) {
    console.error('Ошибка при переотправке заказов:', error);
    throw error;
  }
}