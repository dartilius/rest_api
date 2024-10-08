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
import Search from "@/src/components/Search";
import { PaginationComponent } from "@/src/components/ui/PaginationComponent";
import usePlaylistsQuery from "@/src/hooks/playlists/usePlaylistsQuery";
import Loader from "@/src/components/ui/Loader";
import { toastError } from "@/src/utils/toast-error";
import {useDebounce} from "@/src/hooks/useDebounce";
import styles from './Playlists.module.scss';

export default function Playlists() {
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(10);
  const [name, setName] = useState<string | undefined>(undefined);
  const [openCreatingModal, setOpenCreatingModal] = useState<boolean>(false);
  const debouncedName = useDebounce(name, 500);
  const { data, error, isError, isLoading, isSuccess } = usePlaylistsQuery({
    page,
    limit,
    search: debouncedName,
  });

  const pages = Math.ceil((data?.count || 0) / limit);

  const handleSearchChange = (event: { target: { value: string } }) => {
    setName(event.target.value);
  };

  if (isLoading) {
    return <Loader loading={!isSuccess} />;
  }

  if (isError) {
    return <>{toastError(error?.message)}</>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.container_left}>
        <Button onClick={() => setOpenCreatingModal(true)} color='secondary'>Создать плейлист</Button>
        <Search
            label='Поиск'
            placeholder='Введите название'
            searchValue={name ? name : ""}
            onSearchChange={handleSearchChange}
            onSearchSubmit={() => {}}
        />
      </div>
      <div className={styles.container_right}>
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
      </div>

    </div>
  );
}
