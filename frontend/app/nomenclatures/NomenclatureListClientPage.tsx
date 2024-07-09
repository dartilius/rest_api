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
import { Chip, Select, SelectItem } from "@nextui-org/react";
import Link from "next/link";

import { NomenclaturesService } from "../../services/nomenclatures/nomenclatures.service";
import { NomenclatureListResponseInterface } from "../../types/interface/nomenclature.interface";
import { toastError } from "../../utils/toast-error";

import Loader from "@/components/ui/Loader";
import Search from "@/components/Search";
import { convertStatus } from "@/types/types/checkStatus";
import { limitPages } from "@/types/types/limitPages";
import { timezonesArray } from "@/types/types/timezone";

import styles from './Nomenclature.module.scss'

type Props = {
  data: NomenclatureListResponseInterface;
};

export default function Nomenclatures({ data: initialData }: Props) {
  const [data, setData] = useState<
    NomenclatureListResponseInterface | undefined
  >(undefined);
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(10);
  const [name, setName] = useState<string>("");
  const [status, setStatus] = useState<string>();
  const [zone, setZone] = useState<string>("");
  const [version, setVersion] = useState<string>("");
  const pages = Math.ceil((data?.count || 0) / limit);
  const statusTypes = [0, 1, 2, 3];

  useEffect(() => {
    if (initialData) {
      const fetchData = async () => {
        try {
          const response = await NomenclaturesService.getAll({
            page,
            limit,
            search: name,
            status,
            // timezone: zone,
            versions: version,
          });

          setData(response);
        } catch (error) {
          toastError(error);
        }
      };

      fetchData();
    }
  }, [initialData, page, limit, name, status, version]);

  const handleSearchChange = (event: { target: { value: string } }) => {
    setName(event.target.value);
  };

  const handleSearchSubmit = () => {
    setName(name);
  };

  const handleVersionChange = (event: { target: { value: string } }) => {
    setVersion(event.target.value);
  };

  const handleVersionSubmit = () => {
    setVersion(version);
  };

  if (!data) {
    return <Loader />;
  }

  return (
    <div className={styles.container}>
      <div className={styles.sidebar}>
        <Search
          label="Поиск"
          placeholder="Введите название"
          searchValue={name}
          onSearchChange={handleSearchChange}
          onSearchSubmit={handleSearchSubmit}
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
          defaultSelectedKeys={[`${limit}`]}
          label="Кол-во элементов"
          placeholder="Выберите количество"
          value={limit.toString()} // Ensure default value is a string
          onChange={(e) => setLimit(parseInt(e.target.value))}
        >
          {limitPages.map((option) => (
            <SelectItem key={option.key} value={option.key}>
              {option.label}
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
          searchValue={version}
          onSearchChange={handleVersionChange}
          onSearchSubmit={handleVersionSubmit}
        />
      </div>
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
            <TableColumn>Название</TableColumn>
            <TableColumn>Версия</TableColumn>
            <TableColumn>Последний ответ</TableColumn>
            <TableColumn>Временная зона</TableColumn>
          </TableHeader>
          <TableBody>
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
  );
}
