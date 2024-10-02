import {useMutation, useQuery} from "@tanstack/react-query";

import filesService from "@/src/services/files/files.service";
import nomenclaturesService from "@/src/services/nomenclatures/nomenclatures.service";

export const useFileQuery = (id: string) => {
  const { data, isLoading, error, isError, isSuccess } = useQuery({
    queryKey: ["fileDetails", id],
    queryFn: () => filesService.getById(id),
    select: ({ data }) => data,
  });

  return { data, isLoading, error, isError, isSuccess };
};

export const useFileDeleteMutation = () => {
  const mutation = useMutation({
    mutationKey: ["deleteFile"],
    mutationFn: (id: string) => filesService.deleteById(id),
  });

  return mutation;
};