import { useQuery } from "@tanstack/react-query";

import nomenclaturesService from "@/src/services/nomenclatures/nomenclatures.service";

const useNomenclatureQuery = (id: string) => {
  const { data, isLoading, error, isError, isSuccess } = useQuery({
    queryKey: ["nomenclatureDetails", id],
    queryFn: () => nomenclaturesService.getById(id),
    select: ({ data }) => data,
  });

  console.log('data:', data);


  return { data, isLoading, error, isError, isSuccess };
};

export default useNomenclatureQuery;
