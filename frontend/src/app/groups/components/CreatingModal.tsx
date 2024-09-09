"use client";

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
import { useState } from "react";

import useNomenclaturesQuery from "@/src/hooks/nomenclatures/useNomenclaturesQuery";
import Loader from "@/src/components/ui/Loader";
import groupsService from "@/src/services/groups/groups.service";
import { toastSuccess } from "@/src/utils/toast-success";
import { toastError } from "@/src/utils/toast-error";

type Props = {
  open: boolean;
  close: () => void;
};

const CreatingModal = (props: Props) => {
  const { open, close } = props;
  const [name, setName] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const [owner, setOwner] = useState<string[]>([]);
  const page = 1;
  const limit = 1000;
  const { data } = useNomenclaturesQuery({ page, limit });

  const changeName = (event: React.ChangeEvent<HTMLInputElement>) => {
    setName(event.target.value);
  };
  const changeDescription = (event: React.ChangeEvent<HTMLInputElement>) => {
    setDescription(event.target.value);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      await groupsService.create({
        name,
        description,
        clients: owner,
      });
      close();
      toastSuccess("Группа успешно создана");
      setTimeout(() => {
        window.location.reload();
      }, 2000);
      setName("");
      setDescription("");
      setOwner([]);
    } catch (error) {
      toastError(error);
    }
  };

  console.log("owner:", owner);

  if (!data) {
    return <Loader />;
  }

  return (
    <div>
      <div>
        <Modal isOpen={open} onClose={close}>
          <ModalContent>
            <ModalHeader>Редактирование</ModalHeader>
            <ModalBody>
              <form className="flex flex-col gap-2" onSubmit={handleSubmit}>
                <Input label="Название" value={name} onChange={changeName} />
                <Input
                  label="Описание"
                  value={description}
                  onChange={changeDescription}
                />
                <Select label="Клиенты" selectionMode="multiple">
                  {data.results.map((nomenclature) => (
                    <SelectItem
                      key={nomenclature.id}
                      value={nomenclature.id}
                      onClick={() => setOwner([...owner, nomenclature.id])}
                    >
                      {nomenclature.name}
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

export default CreatingModal;
