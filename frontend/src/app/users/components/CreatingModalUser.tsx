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
import { toastError } from "@/src/utils/toast-error";
import { toastSuccess } from "@/src/utils/toast-success";
import { userRoleChoices } from "@/src/types/types/userRoleChoices";

type Props = {
  open: boolean;
  close: () => void;
};


const CreatingModalUser = (props: Props) => {
  const { open, close } = props;
  const [role, setRole] = useState<string>("");
  const [email, setEmail] = useState<string>("");
  const [phoneNumber, setPhoneNumber] = useState<string>("");

  const changeEmail = (event: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(event.target.value);
  };
  const changePhoneNumber = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPhoneNumber(event.target.value);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      await usersService.create({
        role,
        email,
        username: "bla bvla dhajda",
        phone_number: phoneNumber,
      });
      close();
      toastSuccess("Пользователь успешно создан");
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

  return (
    <div>
      <Modal isOpen={open} onClose={close}>
        <ModalContent>
          <ModalHeader>Создание пользователя</ModalHeader>
          <ModalBody>
            <form className="flex flex-col gap-2" onSubmit={handleSubmit}>
              <Input
                required
                label="Почта"
                type="email"
                value={email}
                onChange={changeEmail}
              />
              <Input
                required
                label="Телефон"
                type="tel"
                value={phoneNumber}
                onChange={changePhoneNumber}
              />
              <Select label="Роль">
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

export default CreatingModalUser;
