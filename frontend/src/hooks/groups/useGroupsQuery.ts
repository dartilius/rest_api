import { useQuery } from "@tanstack/react-query";

import groupsService from "@/src/services/groups/groups.service";

type Props = {
  page: number;
  limit: number;
  search?: string;
  id?: string;
  versions?: string;
  status?: string;
  timezone?: string;
};

const useGroupsQuery = (props: Props) => {
  const { page, limit, search, status, versions, timezone } = props;

  const { data, isLoading, error, isError, isSuccess } = useQuery({
    queryKey: ["groupsList", page, limit, search, status, versions, timezone],
    queryFn: () =>
      groupsService.getAll({
        page,
        limit,
      }),
    select: ({ data }) => data,
  });

  return { data, isLoading, error, isError, isSuccess };
};

export default useGroupsQuery;
