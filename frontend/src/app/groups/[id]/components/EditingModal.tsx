"use client";
import React, { useState } from "react";
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

import { GroupDetailsResponse } from "@/src/types/interface/groups.interface";
import groupsService from "@/src/services/groups/groups.service";
import { toastError } from "@/src/utils/toast-error";
import { toastSuccess } from "@/src/utils/toast-success";
import useNomenclaturesQuery from "@/src/hooks/nomenclatures/useNomenclaturesQuery";
import Loader from "@/src/components/ui/Loader";

type Props = {
  open: boolean;
  close: () => void;
  data: GroupDetailsResponse | undefined;
  id: string;
};

const EditingGroupModal = (props: Props) => {
  const { open, close, data, id } = props;
  const page = 1;
  const limit = 1000;

  const [name, setName] = useState<string | undefined>(data?.name);
  const [description, setDescription] = useState<string | undefined>(
    data?.description,
  );
  const [owner, setOwner] = useState<string[]>(
    data?.clients ? data?.clients.map((v) => v.id) : [],
  );

  const { data: nomenclatures } = useNomenclaturesQuery({ page, limit });

  if (!nomenclatures) {
    return <Loader />;
  }

  const changeName = (event: React.ChangeEvent<HTMLInputElement>) => {
    setName(event.target.value);
  };
  const changeDescription = (event: React.ChangeEvent<HTMLInputElement>) => {
    setDescription(event.target.value);
  };

  const toggleClient = (clientId: string) => {
    setOwner((prevOwner) =>
      prevOwner.includes(clientId)
        ? prevOwner.filter((id) => id !== clientId)
        : [...prevOwner, clientId],
    );
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    try {
      await groupsService.updateById(id, {
        name,
        description,
        clients: owner,
      });
      close();
      toastSuccess("Группа успешно отредактирована");
      setTimeout(() => {
        window.location.reload();
      }, 2000);
    } catch (error) {
      toastError(error);
    }
  };

  return (
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
              <Select
                defaultSelectedKeys={owner} // Assuming `id` is the key property of GroupClients
                label="Клиенты"
                selectionMode="multiple"
              >
                {nomenclatures.results.map((nomenclature) => (
                  <SelectItem
                    key={nomenclature.id}
                    isSelected={owner.includes(nomenclature.id)}
                    value={nomenclature.id}
                    onClick={() => toggleClient(nomenclature.id)}
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
  );
};

export default EditingGroupModal;
