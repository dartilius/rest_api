import { Button } from "@nextui-org/button";
import React, { useEffect, useState } from "react";

import EditingUserModal from "./modal/EditingUserModal";

import { useDeleteUserQuery } from "@/src/hooks/users/useUserQuery";
import { toastError } from "@/src/utils/toast-error";
import { toastSuccess } from "@/src/utils/toast-success";
import DeletingModal from "@/src/components/ui/DeletingModal";

type Props = {
  id: string;
  role: string;
  email: string;
  phoneNumber: string;
};

const UserCardFooter = (props: Props) => {
  const { id, role, email, phoneNumber } = props;
  const [openEditingModal, setOpenEditingModal] = useState<boolean>(false);
  const [openDeletingModal, setOpenDeletingModal] = useState<boolean>(false);

  const {
    mutateAsync: deleteGroup,
    isSuccess: isDeleteSuccess,
    error: deleteError,
    isError: isDeleteError,
  } = useDeleteUserQuery();

  useEffect(() => {
    if (isDeleteSuccess) {
      toastSuccess("Пользователь успешно удален");
      setTimeout(() => {
        window.location.replace("/users");
      }, 2500);
    }
  }, [isDeleteSuccess]);

  const handleDeleteGroup = () => {
    deleteGroup(id);
  };

  const handleCloseDeletingModal = () => {
    setOpenDeletingModal(false);
  };

  const handleCloseEditingModal = () => {
    setOpenEditingModal(false);
  };

  if (isDeleteError) {
    return <>{toastError(deleteError?.message)}</>;
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "12px",
        width: "100%",
      }}
    >
      <Button color="secondary" onClick={() => setOpenEditingModal(true)}>Редактировать</Button>
      <Button color="danger" onClick={() => setOpenDeletingModal(true)}>
        Удалить
      </Button>
      <DeletingModal
        close={handleCloseDeletingModal}
        deleteProp={handleDeleteGroup}
        open={openDeletingModal}
      />
      <EditingUserModal
        close={handleCloseEditingModal}
        emailOld={email}
        id={id}
        open={openEditingModal}
        phoneNumberOld={phoneNumber}
        roleOld={role}
      />
    </div>
  );
};

export default UserCardFooter;
