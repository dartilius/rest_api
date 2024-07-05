"use client";
import { Spinner } from "@nextui-org/spinner";
import { useEffect, useState } from "react";
import {
  Button,
  Pagination,
  Table,
  TableBody,
  TableCell,
  TableColumn,
  TableHeader,
  TableRow,
} from "@nextui-org/react";
import Link from "next/link";

import Search from "../../components/Search";

import FileType from "./components/FileType";
import Tags from "./components/Tags";
import SelectLimit from "./components/SelectLimit";

import { FilesListResponse } from "../../types/interface/files.interface";
import { FilesService } from "../../services/files/files.service";
import { checkSize } from "../../types/types/checkSize";
import { convertType } from "../../types/types/fileTypes";
export default function Files() {
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [limit, setLimit] = useState<number>(10);
  const [page, setPage] = useState<number>(1);
  const [data, setData] = useState<FilesListResponse | undefined>(undefined);
  const [error, setError] = useState<string>("");
  const [search, setSearch] = useState<string>("");
  const [type, setType] = useState<string>("");
  const [inputValue, setInputValue] = useState<string>("");
  const pages = Math.ceil((data?.count || 0) / limit);

  useEffect(() => {
    fetchFiles(page, limit, search, type);
  }, [page, limit, search, type]);

  const fetchFiles = async (
    page: number,
    limit: number,
    name: string,
    type: string,
  ) => {
    setIsLoading(true);
    try {
      const res = await FilesService.getAll({
        page,
        limit,
        name,
        file_type: type,
      });

      setData(res);
      setError("");
    } catch (error: any) {
      setError("Failed to fetch data");
    }
    setIsLoading(false);
  };

  const handleSearchChange = (event: { target: { value: string } }) => {
    setInputValue(event.target.value);
  };

  const handleSearchSubmit = () => {
    setSearch(inputValue);
  };

  const handleTypeChange = (type: string) => {
    setType(type);
  };

  const handleLimitChange = (newLimit: number) => {
    setLimit(newLimit);
    console.log("newLimit:", newLimit);
  };

  if (isLoading) {
    return <Spinner label="Загрузка..." />;
  }

  return (
    <div className="flex flex-row">
      <div className="flex flex-col gap-4 fixed left-48 w-auto h-screen">
        <Search
          label="Поиск"
          placeholder="Поиск"
          searchValue={inputValue}
          onSearchChange={handleSearchChange}
          onSearchSubmit={handleSearchSubmit}
        />
        <FileType setFileType={handleTypeChange} type={type} />
        <Tags />
        <SelectLimit
          label="Лимит"
          limitValue={limit}
          placeholder="Кол-во эл-ов на странице"
          setLimitValue={handleLimitChange}
        />
      </div>
      <div className="ml-48px p-16px grow">
        <Table
          isHeaderSticky
          aria-label="Example table with client side sorting"
          bottomContent={
            <div className="flex justify-center">
              <Pagination
                isCompact
                showControls
                showShadow
                color="secondary"
                page={page}
                total={pages}
                onChange={(page) => setPage(page)}
              />
            </div>
          }
          className="flex flex-col justify-center"
          style={{ width: 640, height: "auto" }}
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
          <TableBody
            isLoading={isLoading}
            loadingContent={<Spinner label="Загрузка..." />}
          >
            {data?.results?.length ? (
              data.results.map((item) => (
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
              ))
            ) : (
              <TableRow>
                <TableCell className="text-center" colSpan={5}>
                  No data available
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <div className="flex flex-col gap-4 fixed right-48 w-auto h-screen">
        <Button
          color="secondary"
          style={{ width: 220, height: 56 }}
          type="button"
        >
          <Link href={`/files/create`} target="_blank">
            Создать
          </Link>
        </Button>
      </div>
    </div>
  );
}
