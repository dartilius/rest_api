import { useMutation, useQuery } from "@tanstack/react-query";

import nomenclaturesService from "@/src/services/nomenclatures/nomenclatures.service";

export const useNomenclatureQuery = (id: string) => {
  const { data, isLoading, error, isError, isSuccess } = useQuery({
    queryKey: ["nomenclatureDetails", id],
    queryFn: () => nomenclaturesService.getById(id),
    select: ({ data }) => data,
  });

  return { data, isLoading, error, isError, isSuccess };
};

export const useDeleteNomenclatureQuery = () => {
  const mutation = useMutation({
    mutationKey: ["deleteNomenclature"],
    mutationFn: (id: string) => nomenclaturesService.deleteById(id),
  });

  return mutation;
};
