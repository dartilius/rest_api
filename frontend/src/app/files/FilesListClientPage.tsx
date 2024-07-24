"use client";
import { useEffect, useState } from "react";
import {
  Button,
  Input,
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

import Search from "../../components/Search";

import styles from "./FilesListClientPage.module.scss";

import { TagsService } from "@/src/services/tags/tags.service";
import { toastError } from "@/src/utils/toast-error";
import { FilesListResponse } from "@/src/types/interface/files.interface";
import Loader from "@/src/components/ui/Loader";
import { convertType, fileTypes } from "@/src/types/types/fileTypes";
import { limitPages } from "@/src/types/types/limitPages";
import { checkSize } from "@/src/types/types/checkSize";
import { PaginationComponent } from "@/src/components/ui/PaginationComponent";
import filesService from "@/src/services/files/files.service";

type Props = {
  data: FilesListResponse;
};

export default function FilesListClientPage({ data: initialData }: Props) {
  const [limit, setLimit] = useState<number>(10);
  const [page, setPage] = useState<number>(1);
  const [data, setData] = useState<FilesListResponse | undefined>(undefined);
  const [search, setSearch] = useState<string>("");
  const [type, setType] = useState<string>("");
  const [inputValue, setInputValue] = useState<string>("");

  const [hash, setHash] = useState<string>("");
  const [tagsList, setTagsList] = useState<string[]>([]);
  const [tags, setTags] = useState<string[]>([]);
  const pages = Math.ceil((data?.count || 0) / limit);

  //TODO: Переписать на useQuery, как в номенклатурах
  useEffect(() => {
    if (initialData) {
      const fetchData = async () => {
        try {
          const responseData = await filesService.getAll()
          const responseTags = await TagsService.gatAll();

          setTagsList(responseTags.results.map((tag) => tag.name));
          setData(responseData.data);
        } catch (error) {
          toastError(error);
        }
      };

      fetchData();
    }
  }, [initialData, page, limit, search, type, tags, hash]);

  const handleSearchChange = (event: { target: { value: string } }) => {
    setInputValue(event.target.value);
  };

  const handleSearchSubmit = () => {
    setSearch(inputValue);
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
          searchValue={search}
          onSearchChange={handleSearchChange}
          onSearchSubmit={handleSearchSubmit}
        />

        <Select
          defaultSelectedKeys={[`${type}`]}
          label="Выберите тип файла"
          onChange={(e) => setType(e.target.value)}
        >
          {fileTypes.map((option) => (
            <SelectItem key={option.key} value={option.key}>
              {option.label}
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
          label="Теги"
          placeholder="Выберите тег"
          value={tagsList} // Ensure default value is a string
          onChange={(e) => setTags([e.target.value])}
        >
          {tagsList.map((option) => (
            <SelectItem key={option} value={option}>
              {option}
            </SelectItem>
          ))}
        </Select>

        <Input
          label="Хэш"
          placeholder="Введите хэш"
          type="text"
          value={hash}
          onChange={(e) => setHash(e.target.value)}
        />

        <Button
          color="secondary"
          style={{ width: 220, height: 56 }}
          type="button"
        >
          <Link href={`/files/create`} target="_blank">
            Создать
          </Link>
        </Button>

        {/*

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
        /> */}
      </div>

      <div style={{ width: 900 }}>
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
            <TableColumn key="name" className="text-center">
              Название
            </TableColumn>
            <TableColumn key="length" className="text-center">
              Длина
            </TableColumn>
            <TableColumn key="size" className="text-center">
              Размер
            </TableColumn>
            <TableColumn key="fileType" className="text-center">
              Тип
            </TableColumn>
            <TableColumn key="tags" className="text-center">
              Тэги
            </TableColumn>
          </TableHeader>
          <TableBody>
            {data.results.map((item) => (
              <TableRow key={item.id} className="text-center">
                <TableCell>
                  <Link href={`/files/${item.id}`} target="_blank">
                    {item.name}
                  </Link>
                </TableCell>
                <TableCell>{item.length}</TableCell>
                <TableCell>{checkSize(item.size)}</TableCell>
                <TableCell>{convertType(item.fileType)}</TableCell>
                <TableCell>{item.tags?.join(", ")}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
