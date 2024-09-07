"use client";

import { useParams } from "next/navigation";
import {
  Button,
  Card,
  CardBody,
  CardFooter,
  CardHeader,
} from "@nextui-org/react";
import { useEffect, useState } from "react";
import Link from "next/link";

import DeletingModal from "../../../components/ui/DeletingModal";

import EditingGroupModal from "./components/EditingModal";

import Loader from "@/src/components/ui/Loader";
import { toastError } from "@/src/utils/toast-error";
import {
  useDeleteGroupQuery,
  useGroupQuery,
} from "@/src/hooks/groups/useGroupQuery";
import { toastSuccess } from "@/src/utils/toast-success";

export default function Page() {
  const router = useParams();
  const id = router?.id;
  const [openDeletingModal, setOpenDeletingModal] = useState<boolean>(false);
  const [openEditingModal, setOpenEditingModal] = useState<boolean>(false);

  const { data, error, isError, isLoading, isSuccess } = useGroupQuery(
    id.toString(),
  );
  const {
    mutateAsync: deleteGroup,
    isSuccess: isDeleteSuccess,
    error: deleteError,
    isError: isDeleteError,
  } = useDeleteGroupQuery();

  useEffect(() => {
    if (isDeleteSuccess) {
      toastSuccess("Группа успешно удалена");
      setTimeout(() => {
        window.location.replace("/groups");
      }, 2500);
    }
  }, [isDeleteSuccess]);

  const handleDeleteGroup = () => {
    deleteGroup(id.toString());
  };

  const handleCloseDeletingModal = () => {
    setOpenDeletingModal(false);
  };

  const handleCloseEditingModal = () => {
    setOpenEditingModal(false);
  };

  if (isLoading) {
    return <Loader loading={!isSuccess} />;
  }
  if (isError) {
    return <>{toastError(error?.message)}</>;
  }
  if (isDeleteError) {
    return <>{toastError(deleteError?.message)}</>;
  }

  return (
    <div
      style={{
        maxWidth: "auto",
        alignItems: "center",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Card style={{ maxWidth: "940px", width: "100%" }}>
        <CardHeader className="flex gap-3 justify-center">
          <div className="flex flex-row items-center gap-1">
            <p className="text-md">Название</p>
            <p className="text-default-500">{data?.name}</p>
          </div>
        </CardHeader>
        <CardBody className="flex items-center">
          <div className="flex flex-row items-center gap-1">
            <p className="text-md">Владелец</p>
            <p className="text-default-500">{data?.owner}</p>
          </div>
          <div className="flex flex-row items-center gap-1">
            <p className="text-md">Описание</p>
            <p className="text-default-500">{data?.description}</p>
          </div>
          <div className="flex flex-row items-center gap-1">
            <p className="text-md">Создана</p>
            <p className="text-default-500">{data?.created}</p>
          </div>
        </CardBody>
        <CardFooter className="flex flex-col justify-center">
          <div>
            <p className="text-md">Клиент(-ы)</p>
          </div>
          {data?.clients.map((client) => (
            <div key={client.id} className="flex flex-row items-center gap-1">
              <Link href={`/nomenclatures/${client.id}`} target="_blank">
                <p className="text-default-500">{client.name}</p>
              </Link>
            </div>
          ))}
        </CardFooter>
      </Card>
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "12px",
          marginTop: "12px",
        }}
      >
        <Button color="primary" onClick={() => setOpenDeletingModal(true)}>
          Удалить
        </Button>
        <Button color="primary" onClick={() => setOpenEditingModal(true)}>
          Редактировать
        </Button>
      </div>
      <DeletingModal
        close={handleCloseDeletingModal}
        deleteProp={handleDeleteGroup}
        open={openDeletingModal}
      />
      <EditingGroupModal
        close={handleCloseEditingModal}
        data={data}
        id={id.toString()}
        open={openEditingModal}
      />
    </div>
  );
}
