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

import useGroupsQuery from "@/src/hooks/groups/useGroupsQuery";
import Loader from "@/src/components/ui/Loader";
import { toastError } from "@/src/utils/toast-error";
import { PaginationComponent } from "@/src/components/ui/PaginationComponent";
import CreatingModal from "./components/CreatingModal";

export default function GroupsListClientPage() {
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(10);
  const [openCreatingModal, setOpenCreatingModal] = useState<boolean>(false);

  const { data, error, isError, isLoading, isSuccess } = useGroupsQuery({
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

  const handleCloseCreatingModal = () => {
    setOpenCreatingModal(false);
  };

  return (
    <>
      <div style={{ maxWidth: "auto" }}>
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
            style={{ maxWidth: "940px" }}
          >
            <TableHeader>
              <TableColumn>Название</TableColumn>
              <TableColumn>количество клиентов</TableColumn>
              <TableColumn>Создана</TableColumn>
            </TableHeader>
            <TableBody>
              {data?.results.map((group) => (
                <TableRow key={group.id}>
                  <TableCell>
                    <Chip variant="bordered">
                      <Link href={`/groups/${group.id}`}>{group.name}</Link>
                    </Chip>
                  </TableCell>
                  <TableCell>{group.clientsCount}</TableCell>
                  <TableCell>{group.created}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
      <CreatingModal
        close={handleCloseCreatingModal}
        open={openCreatingModal}
      />
    </>
  );
}
