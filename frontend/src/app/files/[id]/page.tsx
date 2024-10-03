"use client";

import { useParams } from "next/navigation";
import {
  Card,
  CardBody,
  CardFooter,
  CardHeader,
  Divider,
  Image,
} from "@nextui-org/react";

import { toastError } from "@/src/utils/toast-error";
import Loader from "@/src/components/ui/Loader";
import { checkSize } from "@/src/types/types/checkSize";
import { convertType } from "@/src/types/types/fileTypes";
import useFileQuery from "@/src/hooks/files/useFileQuery";

export default function ReadFile() {
  const router = useParams();
  const id = router?.id;
  const { data, error, isError, isLoading, isSuccess } = useFileQuery(
    id.toString(),
  );

  if (isLoading) {
    return <Loader loading={!isSuccess} />;
  }
  if (isError) {
    return <>{toastError(error?.message)}</>;
  }

  //TODO: Разбить на отдельные компоненты, чтобы не городить вот это вот всё
  return (
    <div>
      <Card className="w-auto">
        <CardHeader className="flex gap-3 justify-center">
          <div className="flex flex-row items-center gap-1">
            <p className="text-md">Название</p>
            <p className="text-default-500">{data?.name}</p>
          </div>
        </CardHeader>
        <Divider />
        <CardBody className="flex items-center">
          <div className="flex flex-row items-center gap-1">
            <p className="text-md">Тэги</p>
            <p className="text-default-500">{data?.tags?.join(", ")}</p>
          </div>
          {data?.length && (
            <div className="flex flex-row items-center gap-1">
              <p className="text-md">Длина</p>
              <p className="text-default-500">{data?.length}</p>
            </div>
          )}
          <div className="flex flex-row items-center gap-1">
            <p className="text-md">Размер</p>
            <p className="text-default-500">{checkSize(data?.size)}</p>
          </div>
          <div className="flex flex-row items-center gap-1">
            <p className="text-md p-0 m-0">Тип</p>
            <p className="text-default-500 p-0 m-0">
              {/*{convertType(data?.fileType)}*/}
            </p>
          </div>
          <Divider />
          <div className="flex flex-col items-center gap-1 flex-wrap">
            <p className="text-md p-0 m-0">Hash</p>
            <div className="flex flex-row items-center gap-1">
              <p className="text-md p-0 m-0">sha256:</p>
              <p className="text-default-500 p-0 m-0">{data?.hash?.sha256}</p>
            </div>
            <div className="flex flex-row items-center gap-1">
              <p className="text-md p-0 m-0">md5:</p>
              <p className="text-default-500 p-0 m-0">{data?.hash?.md5}</p>
            </div>
            <div className="flex flex-row items-center gap-1">
              <p className="text-md p-0 m-0">concatHash:</p>
              <p className="text-default-500 p-0 m-0">
                {data?.hash?.concatHash}
              </p>
            </div>
          </div>
        </CardBody>
        <Divider />
        <CardFooter className="flex justify-center flex-col gap-2">
          <p className="text-md">Заглушка</p>
          <p>не робит</p>
        </CardFooter>
      </Card>
    </div>
  );
}
