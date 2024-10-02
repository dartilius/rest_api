import {useQuery} from "@tanstack/react-query";
import tagsService from "@/src/services/tags/tags.service";

export const useTagsQuery = () => {
    const { data, isLoading, error, isError, isSuccess } = useQuery({
        queryKey: ["tagsList"],
        queryFn: () => tagsService.getAll(),
        select: ({ data }) => data,
    });

    return { data, isLoading, error, isError, isSuccess };
};