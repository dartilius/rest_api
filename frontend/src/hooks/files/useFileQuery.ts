import { useQuery } from "@tanstack/react-query";

import filesService from "@/src/services/files/files.service";

const useFileQuery = (id: string) => {
  const { data, isLoading, error, isError, isSuccess } = useQuery({
    queryKey: ["fileDetails", id],
    queryFn: () => filesService.getById(id),
    select: ({ data }) => data,
  });

  return { data, isLoading, error, isError, isSuccess };
};

export default useFileQuery;
