import { useQuery } from "@tanstack/react-query";

import nomenclaturesService from "@/src/services/nomenclatures/nomenclatures.service";

export const useNomenclaturesList = (page: number, limit: number) => {
  const { data, isLoading, isError, error, isSuccess } = useQuery({
    queryKey: ["nomenclaturesList"],
    queryFn: () => nomenclaturesService.getAll({ page, limit }),
    select: ({ data }) => data,
  });

  return { data, isLoading, isError, error, isSuccess };
};
