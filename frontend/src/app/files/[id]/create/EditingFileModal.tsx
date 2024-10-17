import React, { ChangeEvent, useState } from 'react';
import { Button, Modal, ModalBody, ModalContent, ModalFooter, ModalHeader } from '@nextui-org/react';
import { Select, SelectItem } from '@nextui-org/select';
import { useFileUpdateQuery, useTagsQuery } from '@/src/hooks/files/useFileQuery';
import Loader from '@/src/components/ui/Loader';
import { ITagsListResponseDTO } from '@/src/types/interface/files.interface';

type EditingFileModalProps = {
    tags: ITagsListResponseDTO[] | undefined;
    open: boolean;
    close: () => void;
    id: string;
};

function EditingFileModal(props: EditingFileModalProps) {
    const { tags, open, close, id } = props;
    const page = 1;
    const limit = 1000;
    const { data } = useTagsQuery({ page, limit });
    const [tagsNew, setTagsNew] = useState<string[]>([]);
    const updateFile = useFileUpdateQuery(id);

    if (!data) return <Loader />;

    const validSelectedKeys = tags
        ?.map((tag) => String(tag.id))
        .filter((tagId) => data.results.some((tag) => String(tag.id) === tagId));

    const handleSubmit = async (event: ChangeEvent<HTMLFormElement>) => {
        event.preventDefault();
        updateFile.mutate({tags: tagsNew});
    };

    return (
        <div>
            <Modal isOpen={open} onClose={close}>
                <ModalContent>
                    <ModalHeader>Редактировать файл</ModalHeader>
                    <ModalBody>
                        <form className="flex flex-col gap-2" onSubmit={handleSubmit}>
                            <Select
                                required
                                label="Тэги"
                                selectionMode="multiple"
                                defaultSelectedKeys={validSelectedKeys}
                                onSelectionChange={(selectedKeys) => {
                                    const selectedNames = [...selectedKeys]
                                        .map((key) => data.results.find((tag) => String(tag.id) === key)?.name)
                                        .filter((name): name is string => !!name);
                                    setTagsNew(selectedNames);
                                }}
                            >
                                {data.results.map((tag) => (
                                    <SelectItem key={String(tag.id)} value={String(tag.id)}>
                                        {tag.name}
                                    </SelectItem>
                                ))}
                            </Select>
                            <Button color="secondary" type="submit">Save</Button>
                        </form>
                    </ModalBody>
                </ModalContent>
            </Modal>
        </div>
    );
}

export default EditingFileModal;
