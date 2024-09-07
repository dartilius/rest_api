"use client";

import { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableColumn,
  TableHeader,
  TableRow,
} from "@nextui-org/table";
import Link from "next/link";
import { Button, Chip } from "@nextui-org/react";

import CreatingModalPlaylists from "./components/modal/CreatingModalPlaylists";

import { PaginationComponent } from "@/src/components/ui/PaginationComponent";
import usePlaylistsQuery from "@/src/hooks/playlists/usePlaylistsQuery";
import Loader from "@/src/components/ui/Loader";
import { toastError } from "@/src/utils/toast-error";

export default function Playlists() {
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(10);
  const [openCreatingModal, setOpenCreatingModal] = useState<boolean>(false);

  const { data, error, isError, isLoading, isSuccess } = usePlaylistsQuery({
    page,
    limit,
  });

  const pages = Math.ceil((data?.count || 0) / limit);

  if (isLoading) {
    return <Loader loading={!isSuccess} />;
  }

  if (isError) {
    return <>{toastError(error?.message)}</>;
  }

  return (
    <>
      <Button onClick={() => setOpenCreatingModal(true)}>Создать</Button>
      {data && (
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
            {data.results.map((playlist) => (
              <TableRow key={playlist.id}>
                <TableCell>
                  <Link href={`/playlists/${playlist.id}`}>
                    <Chip color="default">{playlist.name}</Chip>
                  </Link>
                </TableCell>
                <TableCell>{playlist.created}</TableCell>
                <TableCell>{playlist.files_count}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
      <CreatingModalPlaylists
        close={() => setOpenCreatingModal(false)}
        open={openCreatingModal}
      />
    </>
  );
}
