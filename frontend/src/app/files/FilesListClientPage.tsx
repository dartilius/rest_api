"use client";
import { useState } from "react";
import {
  Button, Chip,
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

import { toastError } from "@/src/utils/toast-error";
import Loader from "@/src/components/ui/Loader";
import { convertType, fileTypes } from "@/src/types/types/fileTypes";
import { limitPages } from "@/src/types/types/limitPages";
import { checkSize } from "@/src/types/types/checkSize";
import { PaginationComponent } from "@/src/components/ui/PaginationComponent";
import useFilesQuery from "@/src/hooks/files/useFilesQuery";
import FilesCreate from "@/src/app/files/create/page";
import {useDebounce} from "@/src/hooks/useDebounce";
import {useTagsQuery} from "@/src/hooks/files/useFileQuery";

const colorArray = ['default', 'primary', 'secondary', 'success', 'warning', 'danger'];

const getTagColor = (tag: string) => {
  const hash = tag.split('').reduce((acc, char) => {
    return (acc * 31 + char.charCodeAt(0)) >>> 0;
  }, 0);
  return colorArray[hash % colorArray.length];
};

export default function FilesListClientPage() {
  const [limit, setLimit] = useState<number>(10);
  const [page, setPage] = useState<number>(1);
  const [search, setSearch] = useState<string | undefined>(undefined);
  const [type, setType] = useState<string>("");
  const [inputValue, setInputValue] = useState<string | undefined>(undefined);
  const [openCreatingModal, setOpenCreatingModal] = useState<boolean>(false);
  const [hash, setHash] = useState<string>("");
  const [tags, setTags] = useState<string[] | undefined>(undefined);
  const debouncedName = useDebounce(inputValue, 500);
  const debounceTags = useDebounce(tags, 2000)
  console.log(debouncedName)
  const { data, error, isError, isLoading, isSuccess } = useFilesQuery({
    page,
    limit,
    file_type: type,
    name: debouncedName,
    tags: debounceTags ? debounceTags : []
  });

  const {data: dataTags} = useTagsQuery({page: 1, limit: 1000})

  const listTagsName = dataTags?.results.map((tag) => tag.name)

  const pages = Math.ceil((data?.count || 0) / limit);

  const handleSearchChange = (event: { target: { value: string } }) => {
    setInputValue(event.target.value);
  };

  const handleSearchSubmit = () => {
    setSearch(inputValue);
  };

  if (isLoading) {
    return <Loader loading={!isSuccess} />;
  }

  if (isError) {
    return <>{toastError(error?.message)}</>;
  }

  return (
    <>

        <div className={styles.container}>
          <div className={styles.sidebar}>
            <Search
                label='Поиск'
                placeholder='Введите название'
                searchValue={inputValue ? inputValue : ""}
                onSearchChange={handleSearchChange}
                onSearchSubmit={() => {}}
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
              label="Теги"
              placeholder="Выберите тег"
              value={listTagsName} // Ensure default value is a string
              onChange={(e) => setTags([e.target.value])}
              selectionMode="multiple"
            >
              {listTagsName ? listTagsName.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              )) : <span>Pusto</span>}
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
              onClick={() => setOpenCreatingModal(true)}
            >
              Создать
            </Button>
          </div>
          {data && (
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
                  <TableRow key={item.id}>
                    <TableCell style={{overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis', maxWidth: '30vw', width: '100%'}}>
                      <Link href={`/files/${item.id}`}>
                        {item.name}
                      </Link>
                    </TableCell>
                    <TableCell>{item.length}</TableCell>
                    <TableCell>{checkSize(item.size)}</TableCell>
                    <TableCell>{convertType(item.file_type)}</TableCell>
                    <TableCell>
                      {item.tags?.map((tag) => (
                          <Chip key={tag} color={getTagColor(tag)}>
                            {tag}
                          </Chip>
                      ))}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

        )}
        </div>
      <FilesCreate open={openCreatingModal} close={() => setOpenCreatingModal(false)} />
    </>
  );
}
