import { useQuery } from "@tanstack/react-query";

import playlistsService from "@/src/services/playlists/playlists.service";

type Props = {
  page: number;
  limit: number;
  search: string;
};

const usePlaylistsQuery = (props: Props) => {
  const { page, limit, search } = props;

  const { data, isLoading, error, isError, isSuccess } = useQuery({
    queryKey: ["playlistsList", page, limit, search],
    queryFn: () =>
      playlistsService.getAll({
        page,
        limit,
        search
      }),
    select: ({ data }) => data,
  });

  return { data, isLoading, error, isError, isSuccess };
};

export default usePlaylistsQuery;
