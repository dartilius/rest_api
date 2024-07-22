"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Card,
  CardBody,
  CardFooter,
  CardHeader,
  Divider,
  Image,
} from "@nextui-org/react";

import { ReadFileResponse } from "@/src/types/interface/files.interface";
import { toastError } from "@/src/utils/toast-error";
import Loader from "@/src/components/ui/Loader";
import { checkSize } from "@/src/types/types/checkSize";
import { convertType } from "@/src/types/types/fileTypes";
import { FilesService } from "@/src/services/files/files.service";

export default function ReadFile() {
  const [data, setData] = useState<ReadFileResponse | undefined>(undefined);
  const router = useParams();
  const id = router?.id;

  //TODO: Переписать на useQuery, как в номенклатурах
  const fetchFileInfo = async (fileId: string | string[]) => {
    try {
      const info = await getFileInfo(fileId);

      if (info) {
        setData(info);
      } else {
        console.error("No data found for ID:", fileId);
      }
    } catch (error: any) {
      console.error("Error fetching file info:", error);
      toastError(error);
    }
  };

  useEffect(() => {
    if (id) {
      fetchFileInfo(id);
    } else {
      console.error("ID is undefined");
    }
  }, [id]);

  if (!data) {
    return <Loader />;
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
              {convertType(data?.fileType)}
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
          <Image
            alt={`${data?.name}`}
            height={240}
            loading="lazy"
            radius="sm"
            src="https://bigpicture.ru/wp-content/uploads/2014/12/luchshie-foto-nedeli-v-dek-2014-0.jpg"
            width={240}
          />
        </CardFooter>
      </Card>
    </div>
  );
}

async function getFileInfo(id: string | string[]) {
  try {
    const res = await FilesService.getById(id);

    return res;
  } catch (error) {
    console.error("Error fetching file info:", error);
    throw error;
  }
}
