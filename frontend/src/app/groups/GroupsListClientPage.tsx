"use client";

import { useEffect, useState } from "react";
import {
  Chip,
  Pagination,
  Select,
  SelectItem,
  Table,
  TableBody,
  TableCell,
  TableColumn,
  TableHeader,
  TableRow,
} from "@nextui-org/react";
import Link from "next/link";

import { GroupsService } from "@/src/services/groups/groups.service";
import { toastError } from "@/src/utils/toast-error";
import { GroupsListResponse } from "@/src/types/interface/groups.interface";
import Loader from "@/src/components/ui/Loader";
import { limitPages } from "@/src/types/types/limitPages";
import { PaginationComponent } from "@/src/components/ui/PaginationComponent";

type Props = {
  data: GroupsListResponse;
};

export default function GroupsListClientPage({ data: initialData }: Props) {
  const [data, setData] = useState<GroupsListResponse | undefined>(undefined);
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(10);
  const pages = Math.ceil((data?.count || 0) / limit);

  //TODO: Переписать на useQuery, как в номенклатурах
  useEffect(() => {
    if (initialData) {
      const fetchData = async () => {
        try {
          const response = await GroupsService.getAll({
            page,
            limit,
          });

          setData(response);
        } catch (error) {
          toastError(error);
        }
      };

      fetchData();
    }
  }, [initialData, page, limit]);

  if (!data) {
    return <Loader />;
  }

  return (
    <div style={{ maxWidth: 900, width: "auto" }}>
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
    </div>
  );
}
