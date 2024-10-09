import {Modal, ModalBody, ModalContent, ModalHeader} from "@nextui-org/react";
import {Select, SelectItem} from "@nextui-org/select";
import {fileTypes} from "@/src/types/types/fileTypes";
import {Input} from "@nextui-org/input";
import {Button} from "@nextui-org/button";
import {IPlaylistFiles} from "@/src/types/interface/playlists.interface";
import useFilesQuery from "@/src/hooks/files/useFilesQuery";
import Loader from "@/src/components/ui/Loader";
import {ChangeEvent, useState} from "react";
import {toastSuccess} from "@/src/utils/toast-success";
import {useUpdatePlaylistQuery} from "@/src/hooks/playlists/usePlaylistQuery";

type Props = {
    open: boolean;
    close: () => void;
    namePlaylist: string | undefined;
    desc: string | undefined;
    filesPlaylist: IPlaylistFiles[] | undefined;
    id: number | undefined;
};

function EditingPlaylistModal(props: Props) {

    const {open, close, desc, filesPlaylist, namePlaylist, id} = props
    const page = 1;
    const limit = 1000;
    if (!namePlaylist || !desc || !filesPlaylist || !id) return <Loader />;
    const { data } = useFilesQuery({ page, limit });
    const [files, setFiles] = useState<string[]>([]);
    const [name, setName] = useState<string>(namePlaylist);
    const [description, setDescription] = useState<string>(desc);

    const updatePlaylist = useUpdatePlaylistQuery(id)


    const changeName = (event: ChangeEvent<HTMLInputElement>) => {
        setName(event.target.value);
    };
    const changeDescription = (event: ChangeEvent<HTMLInputElement>) => {
        setDescription(event.target.value);
    };

    const handleSubmit = async (event: ChangeEvent<HTMLFormElement>) => {
        event.preventDefault();
        updatePlaylist.mutate({ name, description, files });
        close();
    };

    if (!data) {
        return <Loader />;
    }

    return (
        <div>
            <Modal isOpen={open} onClose={close}>
                <ModalContent>
                    <ModalHeader>Редактирование плейлсита</ModalHeader>
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
                                defaultValue={desc}
                                onChange={changeDescription}
                            />
                            <Select
                                required
                                label="Файлы"
                                selectionMode="multiple"
                                defaultSelectedKeys={filesPlaylist?.map((file) => file.id) || []}
                                onSelectionChange={(selectedKeys) => setFiles([...selectedKeys].map(String))} // Преобразуем ключи в строки
                            >
                                {data.results.map((file) => (
                                    <SelectItem
                                        key={file.id}
                                        value={file.id}
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
    );
}

export default EditingPlaylistModal;