"use client";

import {
  Card,
  CardBody,
  CardFooter,
  CardHeader,
  Divider,
} from "@nextui-org/react";
import { useEffect, useState } from "react";
import Link from "next/link";

import { UsersService } from "@/src/services/users/users.service";
import { UserInfo } from "@/src/types/interface/user.interface";
import { toastError } from "@/src/utils/toast-error";
import Loader from "@/src/components/ui/Loader";

type Props = {
  id: string;
  data: UserInfo | undefined;
};

export default function UserClientPage(props: Props) {
  const { data: initialData, id } = props;

  const [data, setData] = useState<UserInfo | undefined>(initialData);

  //TODO: Переписать на useQuery, как в номенклатурах
  useEffect(() => {
    if (!initialData) {
      const fetchUser = async (id: string) => {
        try {
          const response = await UsersService.getById(id);

          if (response) {
            setData(response);
          }
        } catch (error) {
          toastError(error);
        }
      };

      fetchUser(id);
    }
  }, [initialData, id]);

  if (!data) {
    return <Loader />;
  }

  //TODO: Разбить на отдельные компоненты, чтобы не городить вот это вот всё
  return (
    <div>
      <Card className="w-auto">
        <CardHeader className="flex gap-3 justify-center flex-col">
          <div className="flex flex-row items-center gap-1">
            <p className="text-md">Имя</p>
            <p className="text-default-500">{data?.fullName.firstName}</p>
          </div>
          <div className="flex flex-row items-center gap-1">
            <p className="text-md">Фамилия</p>
            <p className="text-default-500">{data?.fullName.lastName}</p>
          </div>
          {data?.fullName.middleName && (
            <div className="flex flex-row items-center gap-1">
              <p className="text-md">Отчество</p>
              <p className="text-default-500">{data?.fullName.middleName}</p>
            </div>
          )}
        </CardHeader>
        <Divider />
        <CardBody className="flex items-center">
          <div className="flex flex-row items-center gap-1">
            <p className="text-md">id</p>
            <p className="text-default-500">{data?.id}</p>
          </div>
          <div className="flex flex-row items-center gap-1">
            <p className="text-md">Email</p>
            <p className="text-default-500">
              <Link href={`mailto:${data?.email}`}>{data?.email}</Link>
            </p>
          </div>
          <div className="flex flex-row items-center gap-1">
            <p className="text-md">Телефон</p>
            <p className="text-default-500">
              <Link href={`tel:${data?.phoneNumber}`}>{data?.phoneNumber}</Link>
            </p>
          </div>
          {data?.role && (
            <div className="flex flex-row items-center gap-1">
              <p className="text-md">Роль</p>
              <p className="text-default-500">{data?.role}</p>
            </div>
          )}
          <div className="flex flex-row items-center gap-1">
            <p className="text-md">Создан</p>
            <p className="text-default-500">{data?.created}</p>
          </div>
        </CardBody>
        <Divider />
        <CardFooter className="flex justify-center flex-col gap-2">
          <p className="text-md">Заглушка</p>
          <p className="text-default-500">Заглушка</p>
        </CardFooter>
      </Card>
    </div>
  );
}
