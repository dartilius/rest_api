import { useInfiniteQuery, useQuery } from "@tanstack/react-query";

import filesService from "@/src/services/files/files.service";

type Props = {
  page?: number;
  limit: number;
  name?: string;
  file_type?: string;
  tags?: string[];
  hash?: string;
};

export const useFilesQuery = (props: Props) => {
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


export const useInfiniteFilesQuery = (props: Props) => {
  const { limit, page, name, file_type, tags, hash } = props;

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['infiniteFilesList', limit, file_type, tags, name, hash], // Добавляем параметры в queryKey
    queryFn: ({ pageParam = page || 1 }) => filesService.getAll({
      page: pageParam,
      limit,
      name,
      file_type,
      tags,
      hash,
    }),
      getNextPageParam: (lastPage, allPages) => {
        return lastPage.data.results.length === limit ? allPages.length + 1 : undefined;
      },
      initialPageParam: page || 1,
  });

  return { data, fetchNextPage, hasNextPage, isFetchingNextPage };
};