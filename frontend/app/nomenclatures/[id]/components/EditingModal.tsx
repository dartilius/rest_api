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

import styles from "./EditingModal.module.scss";

import { NomenclatureInterface } from "@/types/interface/nomenclature.interface";
import { NomenclaturesService } from "@/services/nomenclatures/nomenclatures.service";
import { toastError } from "@/utils/toast-error";
import { toastSuccess } from "@/utils/toast-success";
import { timezonesArray } from "@/types/types/timezone";

type Props = {
  open: boolean;
  close: () => void;
  data: NomenclatureInterface;
  id: string;
};

const EditingModal = (props: Props) => {
  const { open, close, data, id } = props;
  const [name, setName] = useState<string>(data.name);
  const [description, setDescription] = useState<string>(data.description);
  const [zone, setZone] = useState<string>(data.timezone);

  console.log(zone);

  const [loading, setLoading] = useState<boolean>(false);

  const changeName = (event: React.ChangeEvent<HTMLInputElement>) => {
    setName(event.target.value);
  };

  const changeDescription = (event: React.ChangeEvent<HTMLInputElement>) => {
    setDescription(event.target.value);
  };

  const changeZone = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setZone(event.target.value);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    try {
      setLoading(true);
      await NomenclaturesService.editById(id, {
        name,
        description,
        timezone: zone,
      });
      close();
      setLoading(false);
      toastSuccess("Номенклатура успешно отредактирована");
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (err) {
      toastError(err);
    }
  };

  return (
    <div >
      <Modal isOpen={open} onClose={close} className={styles.container}>
        <ModalContent>
          <ModalHeader>Редактирование</ModalHeader>
          <ModalBody>
            <form className="flex flex-col gap-2" onSubmit={handleSubmit}>
              <Input label="Название" value={name} onChange={changeName} />
              <Input
                label="Название"
                value={description}
                onChange={changeDescription}
              />
              <Select
                label="Временная зона"
                placeholder="Выберите зону"
                value={zone}
                onChange={changeZone}
              >
                {timezonesArray.map((option) => (
                  <SelectItem key={option.value} value={option.label}>
                    {option.label}
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

export default EditingModal;
