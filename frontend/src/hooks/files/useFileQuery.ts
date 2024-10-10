import {useMutation, useQuery, useQueryClient} from "@tanstack/react-query";

import filesService from "@/src/services/files/files.service";
import {toastError} from "@/src/utils/toast-error";
import {toastSuccess} from "@/src/utils/toast-success";
import {useRouter} from "next/navigation";

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

type tagsQueryType = {
  page: number;
  limit: number;
}

export const useTagsQuery = (props: tagsQueryType) => {
  const {page, limit} = props
  const {data, isError, error, isLoading} = useQuery({
    queryKey: ['tagsList'],
    queryFn: () => filesService.getALlTags({page, limit}),
    select: ({ data }) => data,
  })

  return {data, isLoading, error, isError}
}

export const useFileUpdateQuery = (id: string) => {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationKey: ['updateFile', id],
    mutationFn: (data: any) => filesService.updateById(id, data),
    onSuccess: () => {
      toastSuccess(`Файл успешно Обновлен`);
      queryClient.invalidateQueries({queryKey: ["fileDetails", "filesList", id]});
    },
    onError: (e: any) => {
      console.log(e)
      toastError(`Не обновить файл: ${e.response.details}`);
    }
  })
  return mutation
}

export const useDeleteFileQuery = () => {
  const router = useRouter()
  const mutation = useMutation({
    mutationKey: ['deleteFile'],
    mutationFn: (id: string) => filesService.deleteById(id),
    onSuccess: () => {
      toastSuccess(`Файл успешно удален` )
      router.replace('/files')
    },
    onError: (e: any) => {
      console.log(e)
      toastError(`${e}`)
    }
  })
  return mutation
}