"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableColumn,
  TableHeader,
  TableRow,
} from "@nextui-org/table";
import { Chip } from "@nextui-org/react";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import nomenclaturesService from "@/src/services/nomenclatures/nomenclatures.service";
import { PaginationComponent } from "@/src/components/ui/PaginationComponent";
import Loader from "@/src/components/ui/Loader";
import { toastError } from "@/src/utils/toast-error";

export default function NomenclaturesList() {
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(10);

  const { data, isLoading, isError, error, isSuccess } = useQuery({
    queryKey: ["nomenclaturesList", page, limit],
    queryFn: () => nomenclaturesService.getAll({ page, limit }),
    select: ({ data }) => data,
  });

  if (isLoading) {
    return <Loader loading={!isSuccess} />;
  }

  if (isError) {
    return <>{toastError(error.message)}</>;
  }

  const pages = Math.ceil((data?.count || 0) / limit);

  return (
    <>
      {data ? (
        <div>
          <Table
            isHeaderSticky
            aria-label="Example table with static content"
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
              <TableColumn>title</TableColumn>
              <TableColumn>completed</TableColumn>
            </TableHeader>
            <TableBody>
              {data.results.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>
                    {item.status ? (
                      <Chip color="success">true</Chip>
                    ) : (
                      <Chip color="warning">false</Chip>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <p>Нет данных</p>
      )}
    </>
  );
}
