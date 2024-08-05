import { useMutation, useQuery } from "@tanstack/react-query";

import groupsService from "@/src/services/groups/groups.service";

export const useGroupQuery = (id: string) => {
  const { data, isLoading, error, isError, isSuccess } = useQuery({
    queryKey: ["groupDetails", id],
    queryFn: () => groupsService.getById(id),
    select: ({ data }) => data,
  });

  return { data, isLoading, error, isError, isSuccess };
};

export const useDeleteGroupQuery = () => {
  const mutation = useMutation({
    mutationKey: ["deleteGroup"],
    mutationFn: (id: string) => groupsService.deleteById(id),
  });

  return mutation;
};
