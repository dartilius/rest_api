"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableColumn,
  TableHeader,
  TableRow,
} from "@nextui-org/table";
import { Chip, Select, SelectItem } from "@nextui-org/react";
import { useState } from "react";
import Link from "next/link";

import styles from "./Nomenclature.module.scss";

import { PaginationComponent } from "@/src/components/ui/PaginationComponent";
import Loader from "@/src/components/ui/Loader";
import { toastError } from "@/src/utils/toast-error";
import useNomenclaturesQuery from "@/src/hooks/nomenclatures/useNomenclaturesQuery";
import Search from "@/src/components/Search";
import { convertStatus } from "@/src/types/types/checkStatus";
import { limitPages } from "@/src/types/types/limitPages";
import { timezonesArray } from "@/src/types/types/timezone";
import { useDebounce } from "@/src/hooks/useDebounce";

export default function NomenclaturesList() {
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(10);
  const [name, setName] = useState<string | undefined>(undefined);
  const [status, setStatus] = useState<string>();
  const [zone, setZone] = useState<string>("");
  const [version, setVersion] = useState<string | undefined>(undefined);
  const statusTypes = [0, 1, 2, 3];

  // Использование useDebounce для задержки запросов
  const debouncedName = useDebounce(name, 500);
  const debouncedStatus = useDebounce(status, 500);
  const debouncedZone = useDebounce(zone, 500);
  const debouncedVersion = useDebounce(version, 500);

  const { data, isLoading, error, isError, isSuccess } = useNomenclaturesQuery({
    page,
    limit,
    search: debouncedName,
    status: debouncedStatus,
    versions: debouncedVersion,
    timezone: debouncedZone,
  });

  // if (isLoading) {
  //   return <Loader loading={!isSuccess} />;
  // }

  if (isError) {
    return <>{toastError(error?.message)}</>;
  }

  const pages = Math.ceil((data?.count || 0) / limit);

  const handleSearchChange = (event: { target: { value: string } }) => {
    setName(event.target.value);
  };

  const handleVersionChange = (event: { target: { value: string } }) => {
    setVersion(event.target.value);
  };

  return (
    <>
      {data && (
        <div className={styles.container}>
          <div className={styles.sidebar}>
            <Search
              label="Поиск"
              placeholder="Введите название"
              searchValue={name ? name : ""}
              onSearchChange={handleSearchChange}
              onSearchSubmit={() => {}} // Submit обработчик теперь не нужен
            />

            <Select
              defaultSelectedKeys={[`${status}`]}
              label="Статус"
              onChange={(event) => {
                setStatus(event.target.value);
              }}
            >
              {statusTypes.map((item) => (
                <SelectItem key={item !== null ? item.toString() : ""}>
                  {convertStatus(item)}
                </SelectItem>
              ))}
            </Select>

            <Select
              defaultSelectedKeys={[zone]}
              label="Временная зона"
              placeholder="Выберите зону"
              value={zone} // Ensure default value is a string
              onChange={(e) => setZone(e.target.value)}
            >
              {timezonesArray.map((option) => (
                <SelectItem key={option.value} value={option.label}>
                  {option.label}
                </SelectItem>
              ))}
            </Select>

            <Search
              label="Версия"
              placeholder="Введите версию"
              searchValue={version ? version : ""}
              onSearchChange={handleVersionChange}
              onSearchSubmit={() => {}} // Submit обработчик теперь не нужен
            />
          </div>

          <div>
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
                <TableColumn>Название</TableColumn>
                <TableColumn>Версия</TableColumn>
                <TableColumn>Последний ответ</TableColumn>
                <TableColumn>Временная зона</TableColumn>
              </TableHeader>
              <TableBody
                emptyContent={"Нет данных для отображения."}
                isLoading={!isSuccess}
                loadingContent={<Loader loading={!isSuccess} />}
              >
                {data.results.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      <Link href={`/nomenclatures/${item.id}`} target="_blank">
                        {item.status === 0 && (
                          <Chip color="success" variant="bordered">
                            {item.name}
                          </Chip>
                        )}
                        {item.status === 1 && (
                          <Chip color="warning" variant="bordered">
                            {item.name}
                          </Chip>
                        )}
                        {item.status === 2 && (
                          <Chip color="danger" variant="bordered">
                            {item.name}
                          </Chip>
                        )}
                        {item.status === null && (
                          <Chip color="default" variant="bordered">
                            {item.name}
                          </Chip>
                        )}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Link href={`/nomenclatures/${item.id}`} target="_blank">
                        {item.version}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Link href={`/nomenclatures/${item.id}`} target="_blank">
                        {item.last_answer}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Link href={`/nomenclatures/${item.id}`} target="_blank">
                        {item.timezone}
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      )}
    </>
  );
}
