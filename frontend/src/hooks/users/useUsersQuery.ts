import { useQuery } from "@tanstack/react-query";

import usersService from "@/src/services/users/users.service";

type Props = {
  page: number;
  limit: number;
  search?: string;
  id?: string;
  versions?: string;
  status?: string;
  timezone?: string;
};

const useUsersQuery = (props: Props) => {
  const { page, limit } = props;

  const { data, isLoading, error, isError, isSuccess } = useQuery({
    queryKey: ["usersList", page, limit],
    queryFn: () =>
      usersService.getAll({
        page,
        limit,
      }),
    select: ({ data }) => data,
  });

  return { data, isLoading, error, isError, isSuccess };
};

export default useUsersQuery;
