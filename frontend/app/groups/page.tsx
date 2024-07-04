"use client";

import { useEffect, useState } from "react";
import {
  Chip,
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

import { GroupsService } from "../../services/groups/groups.service";
import { GroupsListResponse } from "../../types/interface/groups.interface";
import { toastError } from "../../utils/toast-error";

export default function PricingPage() {
  const [data, setData] = useState<GroupsListResponse | undefined>(undefined);
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(10);
  const pages = Math.ceil((data?.count || 0) / limit);

  const fetchGroups = async (page: number, limit: number) => {
    try {
      const response = await GroupsService.getAll({ page, limit });

      if (response) {
        setData(response);
      }
    } catch (error) {
      toastError(error);
    }
  };

  useEffect(() => {
    fetchGroups(page, limit);
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
          <TableColumn>количество клиентов</TableColumn>
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
              <TableCell>{group.clientsCount}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  );
}