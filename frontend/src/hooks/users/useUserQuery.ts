import { useMutation, useQuery } from "@tanstack/react-query";

import usersService from "@/src/services/users/users.service";

export const useUserQuery = (id: string) => {
  const { data, isLoading, error, isError, isSuccess, refetch } = useQuery({
    queryKey: ["userDetails", id],
    queryFn: () => usersService.getById(id),
    select: ({ data }) => data,
  });

  return { data, isLoading, error, isError, isSuccess, refetch };
};

export const useDeleteUserQuery = () => {
  const mutation = useMutation({
    mutationKey: ["deleteUser"],
    mutationFn: (id: string) => usersService.deleteById(id),
  });

  return mutation;
};
