"use client";

import { useEffect, useState } from "react";
import {
  Chip,
  Table,
  TableBody,
  TableCell,
  TableColumn,
  TableHeader,
  TableRow,
} from "@nextui-org/react";

import { TaskListResponse } from "@/src/types/interface/tasks.interface";
import { TasksService } from "@/src/services/tasks/tasks.service";
import { toastError } from "@/src/utils/toast-error";
import { PaginationComponent } from "@/src/components/ui/PaginationComponent";
import Loader from "@/src/components/ui/Loader";

export default function Tasks() {
  const [data, setData] = useState<TaskListResponse | undefined>(undefined);
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(10);
  const pages = Math.ceil((data?.count || 0) / limit);

  //TODO: Переписать на useQuery, как в номенклатурах
  const fetchTasks = async (page: number, limit: number) => {
    try {
      const response = await TasksService.getAll({ page, limit });

      if (response) {
        setData(response);
      }
    } catch (error) {
      toastError(error);
    }
  };

  useEffect(() => {
    fetchTasks(page, limit);
  }, [page, limit]);

  if (!data) {
    return <Loader />;
  }

  return (
    <div style={{ width: 900 }}>
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
          <TableColumn>Рабочая станция</TableColumn>
          <TableColumn>Ответственный</TableColumn>
          <TableColumn>Тип</TableColumn>
          <TableColumn>Дата создания</TableColumn>
          <TableColumn>Дата выполнения</TableColumn>
          <TableColumn>Status</TableColumn>
        </TableHeader>
        <TableBody>
          {data.results.map((task) => (
            <TableRow key={task.id}>
              <TableCell>
                {task.status === 0 && (
                  <Chip color="default" variant="bordered">
                    {task.client.name}
                  </Chip>
                )}
                {task.status === 1 && (
                  <Chip color="warning" variant="bordered">
                    {task.client.name}
                  </Chip>
                )}
                {task.status === 2 && (
                  <Chip color="success" variant="bordered">
                    {task.client.name}
                  </Chip>
                )}
                {task.status === 3 && (
                  <Chip color="secondary" variant="bordered">
                    {task.client.name}
                  </Chip>
                )}
                {task.status === 4 && (
                  <Chip color="danger" variant="bordered">
                    {task.client.name}
                  </Chip>
                )}
              </TableCell>
              <TableCell>{task.owner.fullName}</TableCell>
              <TableCell>{task.type}</TableCell>
              <TableCell>{task.created}</TableCell>
              <TableCell>{task.updated}</TableCell>
              <TableCell>{task.status}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
