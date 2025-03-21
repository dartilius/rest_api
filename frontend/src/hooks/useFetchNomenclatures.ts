import {
  INomenclatureByIdResponse,
} from "@/interfaces/Nomenclatures.interface";
import { useQuery } from "@tanstack/react-query";
import {NomenclaturesService} from "@/services/NomenclaturesService";

const nomenclaturesService = new NomenclaturesService()

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