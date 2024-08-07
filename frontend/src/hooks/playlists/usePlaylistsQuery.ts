import { useQuery } from "@tanstack/react-query";

import playlistsService from "@/src/services/playlists/playlists.service";

type Props = {
  page: number;
  limit: number;
};

const usePlaylistsQuery = (props: Props) => {
  const { page, limit } = props;

  const { data, isLoading, error, isError, isSuccess } = useQuery({
    queryKey: ["playlistsList", page, limit],
    queryFn: () =>
      playlistsService.getAll({
        page,
        limit,
      }),
    select: ({ data }) => data,
  });

  return { data, isLoading, error, isError, isSuccess };
};

export default usePlaylistsQuery;
