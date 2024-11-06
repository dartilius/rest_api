import {useMutation, useQuery} from "@tanstack/react-query";
import ordersService from "@/src/services/orders/orders.service";
import {IBgOrderCreate} from "@/src/types/interface/orders.interface";
import {toastSuccess} from "@/src/utils/toast-success";

type Props = {
    page: number;
    limit: number;
    search?: string;
    id?: string;
    versions?: string;
    status?: string;
    timezone?: string;
};

export const useBgOrdersQuery = (props: Props) => {
    const { page, limit } = props;

    const { data, isLoading, error, isError, isSuccess } = useQuery({
        queryKey: ['bgOrders', page, limit],
        queryFn: () =>
            ordersService.background().gatAll({
                page,
                limit
            }),
        select: ({ data }) => data,
    });

    return { data, isLoading, error, isError, isSuccess };
};

export const useBgOrderCreateQuery = () => {
    const mutation = useMutation({
        mutationKey: ['createBgOrder'],
        mutationFn: (data: IBgOrderCreate[]) => ordersService.background().create(data),
        onSuccess: () => {
            toastSuccess('Заказ создан')
        }
    })
    return mutation;
}