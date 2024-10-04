import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import playlistsService from "@/src/services/playlists/playlists.service";
import {toastSuccess} from "@/src/utils/toast-success";
import {toastError} from "@/src/utils/toast-error";

export const usePlaylistQuery = (id: string) => {
  const { data, isLoading, error, isError, isSuccess, refetch } = useQuery({
    queryKey: ["playlistDetails", id],
    queryFn: () => playlistsService.getById(id),
  });

  return { data, isLoading, error, isError, isSuccess, refetch };
};

export const useDeleteUserQuery = () => {
  const mutation = useMutation({
    mutationKey: ["deletePlaylist"],
    mutationFn: (id: string) => playlistsService.deleteById(id),
  });

  return mutation;
};

export const useCreatePlaylistQuery = () => {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationKey: ["createPlaylist"],
    mutationFn: (data: any) => playlistsService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["playlistsList"] });
    },
  });

  return mutation;
};


export const useUpdatePlaylistQuery = (id: number) => {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationKey: ["updatePlaylist"],
    mutationFn: (data: any) => playlistsService.updateById(id, data),
    onSuccess: (data: any) => {
      toastSuccess(`Плейлист \`${data.name} успешно обновлен` )
      queryClient.invalidateQueries({ queryKey: ["playlistDetails"] });
    },
    onError: (error) => {
      console.log(error)
      toastError(`${error}`)
    }
  })

  return mutation
}