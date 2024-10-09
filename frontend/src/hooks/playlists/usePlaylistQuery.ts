import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import playlistsService from "@/src/services/playlists/playlists.service";
import {toastSuccess} from "@/src/utils/toast-success";
import {toastError} from "@/src/utils/toast-error";
import {useRouter} from "next/navigation";

export const usePlaylistQuery = (id: string) => {
  const { data, isLoading, error, isError, isSuccess, refetch } = useQuery({
    queryKey: ["playlistDetails", id],
    queryFn: () => playlistsService.getById(id),
  });

  return { data, isLoading, error, isError, isSuccess, refetch };
};

export const useDeleteUserQuery = () => {
  const router = useRouter()
  const mutation = useMutation({
    mutationKey: ["deletePlaylist"],
    mutationFn: (id: number) => playlistsService.deleteById(id),
    onSuccess: () => {
      toastSuccess(`Плейлист успешно удален` )
      router.replace('/playlists')
    },
    onError: (error) => {
      console.log(error)
      toastError(`${error}`)
    }
  });

  return mutation;
};

export const useCreatePlaylistQuery = () => {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationKey: ["createPlaylist"],
    mutationFn: (data: any) => playlistsService.create(data),
    onSuccess: () => {
      toastSuccess(`Плейлист успешно здан` )
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
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ["playlistDetails"] });
      }, 1500)
    },
    onError: (error) => {
      console.log(error)
      toastError(`${error}`)
    }
  })

  return mutation
}