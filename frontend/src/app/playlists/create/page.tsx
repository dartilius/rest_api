'use client';
import { ChangeEvent, useState, useRef, useCallback, useMemo, useEffect } from "react";
import {
  Button,
  Input,
} from "@nextui-org/react";
import Loader from "@/src/components/ui/Loader";
import { useInfiniteFilesQuery } from "@/src/hooks/files/useFilesQuery";
import { useCreatePlaylistQuery } from "@/src/hooks/playlists/usePlaylistQuery";
import { useDebounce } from "@/src/hooks/useDebounce";
import { FileResponse } from "@/src/types/interface/files.interface";

const CreatelPlaylists = () => {
  const [name, setName] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]); // Состояние для отслеживания выбранных файлов
  const [searchQuery, setSearchQuery] = useState<string>("");

  const debouncedSearchQuery = useDebounce(searchQuery, 1500);

  const fileQueryProps = useMemo(() => ({
    name: debouncedSearchQuery,
    page: 1,
    limit: 10,
  }), [debouncedSearchQuery]);

  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteFilesQuery(fileQueryProps);

  const handleSearchChange = (event: ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(event.target.value);
  };
  
  const [filteredFiles, setFilteredFiles] = useState<FileResponse[]>([]);

  useEffect(() => {
    if (data) {
      const files = data.pages
        .flatMap((page) => page.data.results)
        .filter((file) => file.name.toLowerCase().includes(debouncedSearchQuery.toLowerCase()));
      setFilteredFiles(files);
    }
  }, [data, debouncedSearchQuery]);

  const createPlaylist = useCreatePlaylistQuery();
  const observer = useRef<IntersectionObserver | null>(null);

  const lastFileRef = useCallback(
    (node: HTMLElement | null) => {
      if (isFetchingNextPage) return;

      if (observer.current) observer.current.disconnect();

      observer.current = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && hasNextPage) {
          fetchNextPage();
        }
      });

      if (node) observer.current.observe(node);
    },
    [isFetchingNextPage, fetchNextPage, hasNextPage]
  );

  const changeName = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setName(event.target.value);
  }, []);

  const changeDescription = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setDescription(event.target.value);
  }, []);

  const handleSubmit = async (event: ChangeEvent<HTMLFormElement>) => {
    event.preventDefault();
    createPlaylist.mutate({ name, description, files: selectedFiles });
    setName("");
    setDescription("");
    setSelectedFiles([]);
  };

  if (!data) {
    return <Loader />;
  }

  const toggleFileSelection = (fileId: string) => {
    setSelectedFiles((prevFiles) =>
      prevFiles.includes(fileId) ? prevFiles.filter(id => id !== fileId) : [...prevFiles, fileId]
    );
  };

  return (
    <div>
      <h1>Создание плейлиста</h1>
      <form className="flex flex-col gap-2" onSubmit={handleSubmit}>
        <Input
          required
          label="Название"
          value={name}
          onChange={changeName}
        />
        <Input
          label="Описание"
          value={description}
          onChange={changeDescription}
        />
        <div style={{ position: 'relative' }}>
          <Input
            label="Описание"
            list="file-list"
            placeholder="Поиск файла(-ов)"
            onChange={handleSearchChange}
            value={searchQuery ? searchQuery : ''}
          />
          <ul id="file-list" style={{ maxHeight: "200px", overflowY: "auto" }}>
            {filteredFiles.length === 0 ? (
              <li style={{ padding: "8px", textAlign: "center" }}>Нет файлов, соответствующих запросу.</li>
            ) : (
              filteredFiles.map((file, index) => (
                <li
                  key={file.id}
                  ref={index === filteredFiles.length - 1 ? lastFileRef : null}
                  onClick={() => toggleFileSelection(file.id)}
                  style={{
                    cursor: "pointer",
                    padding: "8px",
                    borderBottom: "1px solid #ccc",
                    backgroundColor: selectedFiles.includes(file.id) ? "#e0f7fa" : "transparent" // Меняем фон для выбранных файлов
                  }}
                >
                  {file.name}
                </li>
              ))
            )}
          </ul>
        </div>
        <Button color="secondary" type="submit">
          Сохранить
        </Button>
      </form>
    </div>
  );
};

export default CreatelPlaylists;
