import {
  INomenclatureByIdResponse,
  INomenclaturesService,
} from "@/interfaces/Nomenclatures.interface";
import NomenclaturesService from "@/services/NomenclaturesService";
import { useQuery } from "@tanstack/react-query";

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
      NomenclaturesService.getAll({
        page,
        limit,
        search,
        status,
        timezone,
        version,
      }),
  });

  const nomenclatures = data?.data.results || [];
  const totalItems = data?.data.count || 0;

  return { nomenclatures, isLoading, isError, refetch, error, totalItems };
};

export const useFetchNomenclatureById = (id: string | undefined) => {
  const { data, isLoading, refetch, isError, error } = useQuery({
    queryKey: ["nomenclatureById", id],
    queryFn: () => NomenclaturesService.getById(id),
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
    queryFn: () => NomenclaturesService.getVersions(),
    select: ({ data }) => data,
  });
  const versionsList: IVersions = data || {
    versions: [],
  };
  return { versionsList, isLoading, isError, error };
};
