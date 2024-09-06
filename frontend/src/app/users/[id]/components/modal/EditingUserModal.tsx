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

import usersService from "@/src/services/users/users.service";
import { userRoleChoices } from "@/src/types/types/userRoleChoices";
import { toastError } from "@/src/utils/toast-error";
import { toastSuccess } from "@/src/utils/toast-success";

type Props = {
  id: string;
  roleOld: string;
  emailOld: string;
  phoneNumberOld: string;
  close: () => void;
  open: boolean;
};

const EditingUserModal = (props: Props) => {
  const { roleOld, emailOld, phoneNumberOld, id, close, open } = props;

  const [role, setRole] = useState<string>(roleOld);
  const [email, setEmail] = useState<string>(emailOld);
  const [phoneNumber, setPhoneNumber] = useState<string>(phoneNumberOld);

  const changeEmail = (event: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(event.target.value);
  };
  const changePhoneNumber = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPhoneNumber(event.target.value);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      await usersService.updateById(id, {
        role,
        email,
        phone_number: phoneNumber,
      });
      close();
      toastSuccess("Пользователь успешно изменен");
      setTimeout(() => {
        window.location.reload();
      }, 2000);
      setRole("");
      setEmail("");
      setPhoneNumber("");
    } catch (error) {
      toastError(error);
    }
  };

  const defaultSelectedKey = userRoleChoices
    .find((choice) => choice.value === roleOld)
    ?.id.toString();

  return (
    <div>
      <Modal isOpen={open} onClose={close}>
        <ModalContent>
          <ModalHeader>Изменение пользователя</ModalHeader>
          <ModalBody>
            <form className="flex flex-col gap-2" onSubmit={handleSubmit}>
              <Input
                label="Почта"
                type="email"
                value={email}
                onChange={changeEmail}
              />
              <Input
                label="Номер телефона"
                type="text"
                value={phoneNumber}
                onChange={changePhoneNumber}
              />
              <Select
                defaultSelectedKeys={
                  defaultSelectedKey ? [defaultSelectedKey] : []
                }
                label="Роль"
              >
                {userRoleChoices.map((choice) => (
                  <SelectItem
                    key={choice.id}
                    value={choice.value}
                    onClick={() => setRole(choice.value)}
                  >
                    {choice.display_name}
                  </SelectItem>
                ))}
              </Select>
              <Button color="primary" type="submit">
                Сохранить
              </Button>
            </form>
          </ModalBody>
        </ModalContent>
      </Modal>
    </div>
  );
};

export default EditingUserModal;
