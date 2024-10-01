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
          <audio autoPlay={true} controls src="http://192.168.0.180:9000/local-media/music/%D0%9F%D0%B0%D1%88%D0%B0_%D0%A2%D0%B5%D1%85%D0%BD%D0%B8%D0%BA_%D0%9D%D1%83%D0%B6%D0%B5%D0%BD_%D0%9A%D1%81%D0%B0%D0%BD%D0%B0%D0%BA%D1%81_%D0%BD%D0%BE_%D1%8D%D1%82%D0%BE_%D0%B3%D1%80%D0%B8%D0%B3%D0%BE%D1%80%D0%B8%D0%B0%D0%BD%D1%81%D0%BA%D0%B8%D0%B9_%D1%85%D0%BE%D1%80.mp3?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=jV1io3iRsfHapjDWLZV2%2F20240930%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20240930T075704Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=8d074f618de7a0909b3ef6c82b32bb071f1e2d49dfcc022a1d8dcf2c8b1e2478"></audio>

          {/*<Image*/}
          {/*  alt={`${data?.name}`}*/}
          {/*  height={240}*/}
          {/*  loading="lazy"*/}
          {/*  radius="sm"*/}
          {/*  src="https://bigpicture.ru/wp-content/uploads/2014/12/luchshie-foto-nedeli-v-dek-2014-0.jpg"*/}
          {/*  width={240}*/}
          {/*/>*/}
        </CardFooter>
      </Card>
    </div>
  );
}
