import { useQuery } from "@tanstack/react-query";

import nomenclaturesService from "@/src/services/nomenclatures/nomenclatures.service";

export const useNomenclaturesDetails = (id: string | string[] | undefined) => {
  const { data, isLoading, error, isError, isSuccess } = useQuery({
    queryKey: ["nomenclaturesDetails", id],
    queryFn: () => nomenclaturesService.getById(id),
    select: ({ data }) => data,
  });

  return {
    data,
    isError,
    error,
    isSuccess,
    isLoading,
  };
};
