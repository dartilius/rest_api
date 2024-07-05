"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableColumn,
  TableHeader,
  TableRow,
} from "@nextui-org/table";
import { Pagination } from "@nextui-org/pagination";
import { Chip, Spinner } from "@nextui-org/react";
import Link from "next/link";

import { NomenclaturesService } from "../../services/nomenclatures/nomenclatures.service";
import { NomenclatureListResponseInterface } from "../../types/interface/nomenclature.interface";
import { toastError } from "../../utils/toast-error";

export default function Nomenclatures() {
  const [data, setData] = useState<
    NomenclatureListResponseInterface | undefined
  >(undefined);
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(10);
  const pages = Math.ceil((data?.count || 0) / limit);

  const fetchNomenclatures = useCallback(
    async (page: number, limit: number) => {
      try {
        const response = await NomenclaturesService.getAll({ page, limit });

        console.log("Fetched data:", response);
        if (response) {
          setData(response);
        }
        // setData(response);
      } catch (error) {
        toastError(error);
      }
    },
    [page, limit],
  );

  useEffect(() => {
    fetchNomenclatures(page, limit);
  }, [page, limit]);

  if (!data) {
    return (
      <div className="flex justify-center">
        <Spinner aria-label="Spinner example" />
      </div>
    );
  }

  return (
    <>
      <Table
        isHeaderSticky
        aria-label="Example table with static content"
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
          <TableColumn>Версия</TableColumn>
          <TableColumn>Последний ответ</TableColumn>
          <TableColumn>Временная зона</TableColumn>
        </TableHeader>
        <TableBody>
          {data.results.map((item) => (
            <TableRow key={item.id}>
              <TableCell>
                <Link href={`/nomenclatures/${item.id}`} target="_blank">
                  {item.status === 0 && (
                    <Chip color="success" variant="bordered">
                      {item.name}
                    </Chip>
                  )}
                  {item.status === 1 && (
                    <Chip color="warning" variant="bordered">
                      {item.name}
                    </Chip>
                  )}
                  {item.status === 2 && (
                    <Chip color="danger" variant="bordered">
                      {item.name}
                    </Chip>
                  )}
                  {item.status === null && (
                    <Chip color="default" variant="bordered">
                      {item.name}
                    </Chip>
                  )}
                </Link>
              </TableCell>
              <TableCell>
                <Link href={`/nomenclatures/${item.id}`} target="_blank">
                  {item.version}
                </Link>
              </TableCell>
              <TableCell>
                <Link href={`/nomenclatures/${item.id}`} target="_blank">
                  {item.last_answer}
                </Link>
              </TableCell>
              <TableCell>
                <Link href={`/nomenclatures/${item.id}`} target="_blank">
                  {item.timezone}
                </Link>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  );
}
