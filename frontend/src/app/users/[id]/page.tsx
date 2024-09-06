"use client";
import { Card, CardBody, CardFooter, CardHeader } from "@nextui-org/react";
import { useState } from "react";

import UserCardHeader from "./components/UserCardHeader";
import UserCardBody from "./components/UserCardBody";
import UserCardFooter from "./components/UserCardFooter";

import Loader from "@/src/components/ui/Loader";
import useIdFromParams from "@/src/hooks/useIdFromParams";
import { useUserQuery } from "@/src/hooks/users/useUserQuery";
import { toastError } from "@/src/utils/toast-error";

export default function Page() {
  const id = useIdFromParams();
  const [openDeletingModal, setOpenDeletingModal] = useState<boolean>(false);
  const { data, error, isError, isLoading, isSuccess, refetch } = useUserQuery(id);

  if (isLoading) {
    return <Loader loading={!isSuccess} />;
  }
  if (isError) {
    return <>{toastError(error?.message)}</>;
  }

  if (!data) {
    refetch()
    if (!data) {
      return <>{toastError("Пользователь не найден")}</>;
    }
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
      <Card>
        <CardHeader className="flex gap-3 justify-center">
          <UserCardHeader
            firstName={data.full_name.first_name}
            lastName={data.full_name.last_name}
            middleName={data.full_name.middle_name}
          />
        </CardHeader>
        <CardBody>
          <UserCardBody
            created={data?.created}
            email={data?.email}
            id={id}
            phoneNumber={data?.phone_number}
            role={data?.role}
          />
        </CardBody>
        <CardFooter>
          <UserCardFooter id={id} email={data.email} role={data.role} phoneNumber={data.phone_number}/>
        </CardFooter>
      </Card>
    </div>
  );
}
