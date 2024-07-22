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
import Link from "next/link";
import { Chip, Spinner } from "@nextui-org/react";

import { PlaylistsListResponse } from "@/src/types/interface/playlists.interface";
import { PlaylistsService } from "@/src/services/playlists/playlists.service";
import { toastError } from "@/src/utils/toast-error";
import { PaginationComponent } from "@/src/components/ui/PaginationComponent";

export default function Playlists() {
  const [data, setData] = useState<PlaylistsListResponse | undefined>(
    undefined,
  );
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(10);
  const pages = Math.ceil((data?.count || 0) / limit);

  //TODO: Переписать на useQuery, как в номенклатурах
  const fetchPlaylists = async () => {
    try {
      const res = await PlaylistsService.getAll();

      if (res) {
        setData(res);
      }
    } catch (error) {
      toastError(error);
    }
  };

  useEffect(() => {
    fetchPlaylists();
  }, []);

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
          <TableColumn>название</TableColumn>
          <TableColumn>создан</TableColumn>
          <TableColumn>количество файлов</TableColumn>
        </TableHeader>
        <TableBody>
          {data.results.map((group) => (
            <TableRow key={group.id}>
              <TableCell>
                <Link href={`/groups/${group.id}`}>
                  <Chip color="default">{group.name}</Chip>
                </Link>
              </TableCell>
              <TableCell>{group.created}</TableCell>
              <TableCell>{group.filesCount}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  );
}
