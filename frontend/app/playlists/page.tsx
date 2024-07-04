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
import Link from "next/link";
import { Chip, Spinner } from "@nextui-org/react";

import { toastError } from "../../utils/toast-error";
import { PlaylistsListResponse } from "../../types/interface/playlists.interface";
import { PlaylistsService } from "../../services/playlists/playlists.service";

export default function Playlists() {
  const [data, setData] = useState<PlaylistsListResponse | undefined>(
    undefined,
  );
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(10);
  const pages = Math.ceil((data?.count || 0) / limit);

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
