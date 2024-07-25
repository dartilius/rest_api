"use client";

import { useEffect, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableColumn,
  TableHeader,
  TableRow,
} from "@nextui-org/react";
import Link from "next/link";
import { DatePicker } from "antd";
import dayjs from "dayjs";

import styles from "./UsersList.module.scss";

import { UsersListResponse } from "@/src/types/interface/user.interface";
import { UsersService } from "@/src/services/users/users.service";
import { toastError } from "@/src/utils/toast-error";
import Loader from "@/src/components/ui/Loader";
import "dayjs/locale/ru";
import { PaginationComponent } from "@/src/components/ui/PaginationComponent";
import Search from "@/src/components/Search";
const { RangePicker } = DatePicker;

dayjs.locale("ru");
export default function UsersList() {
  const [data, setData] = useState<UsersListResponse | undefined>(undefined);
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(10);
  const [startDate, setStartDate] = useState<string>("");
  const [name, setName] = useState<string | undefined>(undefined);
  const [endDate, setEndDate] = useState<string>("");
  const pages = Math.ceil((data?.count || 0) / limit);

  //TODO: Переписать на useQuery, как в номенклатурах
  const fetchUsers = async (
    page: number,
    limit: number,
    startDate: string,
    endDate: string,
    name: string | undefined,
  ) => {
    try {
      const response = await UsersService.getAll({
        page,
        limit,
        created_after: startDate,
        created_before: endDate,
        name,
      });

      if (response) {
        setData(response);
      }
    } catch (error) {
      toastError(error);
    }
  };

  const handleSearchChange = (event: { target: { value: string } }) => {
    setName(event.target.value);
  };

  const handleSearchSubmit = () => {
    setName(name);
  };

  useEffect(() => {
    fetchUsers(page, limit, startDate, endDate, name);
  }, [page, limit, startDate, endDate, name]);

  if (!data) {
    return <Loader />;
  }

  const handleDateChange = (value: any) => {
    if (value) {
      const start = dayjs(value[0]).format("YYYY-MM-DD");
      const end = dayjs(value[1]).format("YYYY-MM-DD");

      if (start) {
        setStartDate(start);
      }
      if (end) {
        setEndDate(end);
      }
    } else {
      setStartDate("");
      setEndDate("");
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.sidebar}>
        <Search
          label="Поиск"
          placeholder="Введите название"
          // searchValue={search}
          searchValue={name ? name : ""}
          onSearchChange={handleSearchChange}
          onSearchSubmit={handleSearchSubmit}
        />
        <RangePicker onChange={handleDateChange} />
      </div>
      <div style={{ maxWidth: 960, width: 480 }}>
        <Table
          isHeaderSticky
          aria-label="Example table with static content"
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
            <TableColumn>id</TableColumn>
            <TableColumn>created</TableColumn>
            <TableColumn>fullName</TableColumn>
            <TableColumn>role</TableColumn>
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
                <TableCell>{user.role}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
