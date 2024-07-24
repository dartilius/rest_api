import { useQuery } from "@tanstack/react-query";

import nomenclaturesService from "@/src/services/nomenclatures/nomenclatures.service";

type Props = {
  page: number;
  limit: number;
  search?: string;
  id?: string;
  versions?: string;
  status?: string;
  timezone?: string;
};

const useNomenclaturesQuery = (props: Props) => {
  const { page, limit, search, status, versions, timezone } = props;

  const { data, isLoading, error, isError, isSuccess } = useQuery({
    queryKey: [
      "nomenclaturesList",
      page,
      limit,
      search,
      status,
      versions,
      timezone,
    ],
    queryFn: () =>
      nomenclaturesService.getAll({
        page,
        limit,
        search,
        status,
        versions,
        timezone,
      }),
    select: ({ data }) => data,
  });

  return { data, isLoading, error, isError, isSuccess };
};

export default useNomenclaturesQuery;
