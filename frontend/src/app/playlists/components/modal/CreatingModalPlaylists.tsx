import { ChangeEvent, useState, useRef, useCallback, useMemo } from "react";
import {
  Button,
  Input,
  Modal,
  ModalBody,
  ModalContent,
  ModalHeader,
} from "@nextui-org/react";
import Loader from "@/src/components/ui/Loader";
import { useInfiniteFilesQuery } from "@/src/hooks/files/useFilesQuery";
import { useCreatePlaylistQuery } from "@/src/hooks/playlists/usePlaylistQuery";
import { useDebounce } from "@/src/hooks/useDebounce";

type Props = {
  open: boolean;
  close: () => void;
};

const CreatingModalPlaylists = (props: Props) => {
  const { open, close } = props;
  const [name, setName] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const [files, setFiles] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>(""); // Состояние для поиска
  const searchQueryDebaunce = useDebounce(searchQuery, 500);

  // Используем query для работы с пагинацией
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteFilesQuery({
    page: 1,
    limit: 10,
    name: searchQueryDebaunce,
  });

  const createPlaylist = useCreatePlaylistQuery();
  const observer = useRef<IntersectionObserver | null>(null); // Определяем observer на уровне компонента

  const lastFileRef = useCallback(
    (node: HTMLElement | null) => {
      if (isFetchingNextPage) return;

      // Отключаем предыдущий наблюдатель, если он существует
      if (observer.current) observer.current.disconnect();

      // Создаём новый IntersectionObserver, если его ещё нет
      observer.current = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && hasNextPage) {
          fetchNextPage();
        }
      });

      // Если узел существует, начинаем наблюдение
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

  const handleSearchChange = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(event.target.value); // Обновляем состояние поиска
  }, []);

  const handleSubmit = async (event: ChangeEvent<HTMLFormElement>) => {
    event.preventDefault();
    createPlaylist.mutate({ name, description, files });
    close();
    setName("");
    setDescription("");
    setFiles([]);
  };

  if (!data) {
    return <Loader />;
  }

  // Мемоизация фильтрации файлов для оптимизации перерендеров
  const filteredFiles = data?.pages
      .flatMap((page) => page.data.results)
      .filter((file) => file.name.toLowerCase().includes(searchQueryDebaunce.toLowerCase()));
  

  const addFile = (fileId: string) => {
    setFiles((prevFiles) => [...prevFiles, fileId]); // Обновление файлов с помощью функции
  };

  return (
    <Modal isOpen={open} onClose={close}>
      <ModalContent>
        <ModalHeader>Создание плейлиста</ModalHeader>
        <ModalBody>
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
              <input
                list="file-list"
                placeholder="Поиск файла(-ов)"
                onChange={handleSearchChange}
              />
              {/* Здесь мы заменяем datalist на обычный список */}
              <ul id="file-list" style={{ maxHeight: "200px", overflowY: "auto" }}>
                {filteredFiles.length === 0 ? (
                  <li style={{ padding: "8px", textAlign: "center" }}>Нет файлов, соответствующих запросу.</li>
                ) : (
                  filteredFiles.map((file, index) => (
                    <li
                      key={file.id}
                      ref={index === filteredFiles.length - 1 ? lastFileRef : null} // Применяем ref к последнему элементу
                      onClick={() => addFile(file.id)} // Добавляем файл в массив
                      style={{ cursor: "pointer", padding: "8px", borderBottom: "1px solid #ccc" }}
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
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default CreatingModalPlaylists;
