import {useQuery} from "@tanstack/react-query";
import ordersService from "@/src/services/orders/orders.service";

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
    const 
}