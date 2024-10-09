import {useMutation, useQuery, useQueryClient} from "@tanstack/react-query";

import filesService from "@/src/services/files/files.service";
import playlistsService from "@/src/services/playlists/playlists.service";
import {toastError} from "@/src/utils/toast-error";
import {toastSuccess} from "@/src/utils/toast-success";

const useFileQuery = (id: string) => {
  const { data, isLoading, error, isError, isSuccess } = useQuery({
    queryKey: ["fileDetails", id],
    queryFn: () => filesService.getById(id),
    select: ({ data }) => data,
  });

  return { data, isLoading, error, isError, isSuccess };
};

export default useFileQuery;

export const useCreateFileQuery = () => {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationKey: ["createPlaylist"],
    mutationFn: (data: any) => filesService.create(data),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ["filesList"] });
      toastSuccess(`Файл \`${data.name}\` успешно создан`);
    },
    onError: (e: any) => {
      console.log(e)
      toastError(`Не удалось создать файл: ${e.response.data.tags}`);
    }
  });

  return mutation;
};
