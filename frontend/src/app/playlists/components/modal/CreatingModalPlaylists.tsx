import {ChangeEvent, useState} from "react";
import {
  Button,
  Input,
  Modal,
  ModalBody,
  ModalContent,
  ModalHeader,
  Select,
  SelectItem,
} from "@nextui-org/react";

import Loader from "@/src/components/ui/Loader";
import useFilesQuery from "@/src/hooks/files/useFilesQuery";
import { toastSuccess } from "@/src/utils/toast-success";
import { useCreatePlaylistQuery } from "@/src/hooks/playlists/usePlaylistQuery";

type Props = {
  open: boolean;
  close: () => void;
};

const CreatingModalPlaylists = (props: Props) => {
  const { open, close } = props;
  const [name, setName] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const [files, setFiles] = useState<string[]>([]);
  const page = 1;
  const limit = 1000;
  const { data } = useFilesQuery({ page, limit });
  const createPlaylist = useCreatePlaylistQuery();

  const changeName = (event: ChangeEvent<HTMLInputElement>) => {
    setName(event.target.value);
  };
  const changeDescription = (event: ChangeEvent<HTMLInputElement>) => {
    setDescription(event.target.value);
  };

  const handleSubmit = async (event: ChangeEvent<HTMLFormElement>) => {
    event.preventDefault();
    createPlaylist.mutate({ name, description, files });
    close();
    //   setTimeout(() => {
    //     window.location.reload();
    //   }, 2000);
    setName("");
    setDescription("");
    setFiles([]);
  };

  if (!data) {
    return <Loader />;
  }

  return (
    <div>
      <div>
        <Modal isOpen={open} onClose={close}>
          <ModalContent>
            <ModalHeader>Создание плейлсита</ModalHeader>
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
                <Select required label="Файлы" selectionMode="multiple">
                  {data.results.map((file) => (
                    <SelectItem
                      key={file.id}
                      value={file.id}
                      onClick={() => setFiles([...files, file.id])}
                    >
                      {file.name}
                    </SelectItem>
                  ))}
                </Select>
                <Button color="secondary" type="submit">
                  Сохранить
                </Button>
              </form>
            </ModalBody>
          </ModalContent>
        </Modal>
      </div>
    </div>
  );
};

export default CreatingModalPlaylists;
