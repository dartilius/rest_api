"use client";

import { useEffect, useState } from "react";
import {
  Pagination,
  Spinner,
  Table,
  TableBody,
  TableCell,
  TableColumn,
  TableHeader,
  TableRow,
} from "@nextui-org/react";
import Link from "next/link";

import { UsersListResponse } from "../../types/interface/user.interface";
import { UsersService } from "../../services/users/users.service";
import { toastError } from "../../utils/toast-error";

export default function DocsPage() {
  const [data, setData] = useState<UsersListResponse | undefined>(undefined);
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(10);
  const pages = Math.ceil((data?.count || 0) / limit);

  const fetchUsers = async () => {
    try {
      const response = await UsersService.getAll();

      if (response) {
        setData(response);
      }
    } catch (error) {
      toastError(error);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  if (!data) {
    return (
      <div className="flex justify-center">
        <Spinner aria-label="Spinner example" />
      </div>
    );
  }

  return (
    <div>
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
          <TableColumn>id</TableColumn>
          <TableColumn>created</TableColumn>
          <TableColumn>fullName</TableColumn>
        </TableHeader>
        <TableBody>
          {data.results.map((user) => (
            <TableRow key={user.id}>
              <TableCell>
                <Link href={`/users/${user.id}`} target="_blank">
                  {user.id}
                </Link>
              </TableCell>
              <TableCell>
                <Link href={`/users/${user.id}`} target="_blank">
                  {user.created}
                </Link>
              </TableCell>
              <TableCell>
                <Link href={`/users/${user.id}`} target="_blank">
                  {user.fullName}
                </Link>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
