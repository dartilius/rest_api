"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableColumn,
  TableHeader,
  TableRow,
} from "@nextui-org/table";
import { useState } from "react";

import { useNomenclaturesList } from "../hooks/nomenclatures/useNomenclaturesList";

import { PaginationComponent } from "@/src/components/ui/PaginationComponent";
import Loader from "@/src/components/ui/Loader";
import { toastError } from "@/src/utils/toast-error";

export default function NomenclaturesList() {
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(10);

  const { data, isLoading, isError, error, isSuccess } = useNomenclaturesList(
    page,
    limit,
  );

  if (isLoading) {
    return <Loader loading={!isSuccess} />;
  }

  if (isError) {
    return <>{toastError(error?.message)}</>;
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
                  <TableCell>test</TableCell>
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
