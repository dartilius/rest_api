import {
  INomenclatureByIdResponse,
  INomenclaturesService,
} from "@/interfaces/Nomenclatures.interface";
import { useQuery } from "@tanstack/react-query";
import {NomenclaturesService} from "@/services/NomenclaturesService";
import {API_URL} from "@/config/api.config";
import {getClientAccessToken} from "@/utils";

const nomenclaturesService = new NomenclaturesService()

export const useFetchNomenclatures = ({
  page,
  limit,
  search,
  status,
  timezone,
  version,
}: INomenclaturesService) => {
  const { data, isLoading, isError, refetch, error } = useQuery({
    queryKey: [
      "nomenclaturesList",
      page,
      limit,
      search,
      status,
      timezone,
      version,
    ],
    queryFn: () =>
        nomenclaturesService.getAll({
        page,
        limit,
        search,
        status,
        timezone,
        version,
      }),
  });

  const nomenclatures = data?.results || [];
  const totalItems = data?.count || 0;

  console.log(data)

  return { nomenclatures, isLoading, isError, refetch, error, totalItems };
};

export const useFetchNomenclatureById = (id: string | undefined) => {
  const { data, isLoading, refetch, isError, error } = useQuery({
    queryKey: ["nomenclatureById", id],
    queryFn: () => nomenclaturesService.getById(id),
  });

  if (!data) return { refetch, isError, error };

  const nomenclature: INomenclatureByIdResponse = data.data;

  return { nomenclature, refetch, isError, error, isLoading };
};

export interface IVersions {
  versions: string[];
}

export const useGetVersions = () => {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["getVersionsNomenclatures"],
    queryFn: () => nomenclaturesService.getVersions(),
    select: ({ data }) => data,
    gcTime: 60,
  });
  const versionsList: IVersions = data || {
    versions: [],
  };
  return { versionsList, isLoading, isError, error };
};