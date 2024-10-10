import { useQuery } from "@tanstack/react-query";

import filesService from "@/src/services/files/files.service";

type Props = {
  page: number;
  limit: number;
  name: string;
  file_type?: string;
  tags: string[];
  hash?: string;
};

const useFilesQuery = (props: Props) => {
  const { page, limit, hash, tags, name, file_type } = props;

  const { data, isLoading, error, isError, isSuccess } = useQuery({
    queryKey: ["filesList", page, limit, hash, tags, name, file_type],
    queryFn: () =>
      filesService.getAll({
        page,
        tags,
        limit,
        file_type,
        name,

      }),
    select: ({ data }) => data,
  });

  return { data, isLoading, error, isError, isSuccess };
};

export default useFilesQuery;
