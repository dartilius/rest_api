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
import { Chip } from "@nextui-org/react";
import Link from "next/link";

import { AdOrdersService } from "@/services/ad-orders/AdOrders.service";
import { toastError } from "@/utils/toast-error";
import { AdOrdersListResponse } from "@/types/interface/orders.interface";
import Loader from "@/components/ui/Loader";

export default function AdOrders() {
  const [data, setData] = useState<AdOrdersListResponse | undefined>(undefined);
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(10);
  const pages = Math.ceil((data?.count || 0) / limit);

  const fetchAdOrders = async (page: number, limit: number) => {
    try {
      const res = await AdOrdersService.getAll({ page, limit });

      if (res) {
        setData(res);
      }
    } catch (error) {
      toastError(error);
    }
  };

  useEffect(() => {
    fetchAdOrders(page, limit);
  }, [page, limit]);

  if (!data) {
    return <Loader />;
  }

  return (
    <div>
      <Table
        isHeaderSticky
        bottomContent={
          <div className="flex justify-center">
            <Pagination
              isCompact
              showControls
              showShadow
              color="secondary"
              page={page}
              total={pages}
              onChange={(newPage) => setPage(newPage)}
            />
          </div>
        }
      >
        <TableHeader>
          <TableColumn>Название</TableColumn>
          <TableColumn>Группа</TableColumn>
          <TableColumn>Файл</TableColumn>
          <TableColumn>Слайды</TableColumn>
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
                  <Link href={`/groups/${order.group.id}`} target="_blank">
                    {order.group.name}
                  </Link>
                </Chip>
              </TableCell>
              <TableCell>
                <Chip color="default" variant="bordered">
                  <Link href={`/files/${order.file.id}`} target="_blank">
                    {order.file.name}
                  </Link>
                </Chip>
              </TableCell>
              <TableCell>{order.slides}</TableCell>
              <TableCell>
                {order.broadcastInterval.since}, {order.broadcastInterval.until}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
