import { useQuery } from "@tanstack/react-query";

import filesService from "@/src/services/files/files.service";

type Props = {
  page: number;
  limit: number;
  search?: string;
  id?: string;
  versions?: string;
  status?: string;
  timezone?: string;
};

const useFilesQuery = (props: Props) => {
  const { page, limit, search, status, versions, timezone } = props;

  const { data, isLoading, error, isError, isSuccess } = useQuery({
    queryKey: ["filesList", page, limit, search, status, versions, timezone],
    queryFn: () =>
      filesService.getAll({
        page,
        limit,
      }),
    select: ({ data }) => data,
  });

  return { data, isLoading, error, isError, isSuccess };
};

export default useFilesQuery;
