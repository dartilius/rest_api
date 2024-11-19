"use client";

import { useEffect, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableColumn,
  TableHeader,
  TableRow,
} from "@nextui-org/table";
import { Pagination } from "@nextui-org/pagination";
import {Button, Chip, Select, SelectItem} from "@nextui-org/react";
import Link from "next/link";

import { BgOrdersListResponse } from "@/src/types/interface/orders.interface";
import { toastError } from "@/src/utils/toast-error";
import Loader from "@/src/components/ui/Loader";
import { limitPages } from "@/src/types/types/limitPages";
import { PaginationComponent } from "@/src/components/ui/PaginationComponent";
import ordersService from "@/src/services/orders/orders.service";
import { useBgOrdersQuery } from "@/src/hooks/orders/useBgOrdersQuery";

export default function BgOrders() {
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(10);
  const {data} = useBgOrdersQuery({page, limit})
  const pages = Math.ceil((data?.count || 0) / limit);

  if (!data) {
    return <Loader />;
  }

  return (
    <div>
      <Link href={'/orders/create/'}>
        <Button color='secondary'>Создать</Button>
      </Link>
      <Table
        isHeaderSticky
        bottomContent={
          <PaginationComponent
            limit={limit}
            page={page}
            total={pages}
            onLimitChange={setLimit}
            onPageChange={setPage}
          />
        }
      >
        <TableHeader>
          <TableColumn>Название</TableColumn>
          <TableColumn>Клиент</TableColumn>
          <TableColumn>Плейлист</TableColumn>
          <TableColumn>Интервал</TableColumn>
        </TableHeader>
        <TableBody>
          {data?.results.map((order) => (
            <TableRow key={order.id}>
              <TableCell>
                <Chip color="default" variant="bordered">
                  <Link href={`/orders/${order.id}`} target="_blank">
                    {order.name}
                  </Link>
                </Chip>
              </TableCell>
              <TableCell>
                <Chip color="default" variant="bordered">
                  <Link href={`/nomenclatures/${order.client.id}`} target="_blank">
                    {order.client.name}
                  </Link>
                </Chip>
              </TableCell>
              <TableCell>
                <Chip color="default" variant="bordered">
                  <Link
                    href={`/playlists/${order.playlist.id}`}
                    target="_blank"
                  >
                    {order.playlist.id}
                  </Link>
                </Chip>
              </TableCell>
              <TableCell>
                {order.broadcastInterval?.since}, {order.broadcastInterval?.until}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
