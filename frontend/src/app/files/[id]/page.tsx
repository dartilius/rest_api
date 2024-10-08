"use client";

import { useParams } from "next/navigation";

import { toastError } from "@/src/utils/toast-error";
import Loader from "@/src/components/ui/Loader";
import useFileQuery from "@/src/hooks/files/useFileQuery";
import {getMediaType} from "@/src/types/types/getMediaType";

import styles from './FileDesc.module.scss'
import {checkSize} from "@/src/types/types/checkSize";
import {Image} from "@nextui-org/react";

export default function ReadFile() {
  const router = useParams();
  const id = router?.id;
  const { data, error, isError, isLoading, isSuccess } = useFileQuery(
    id.toString(),
  );

  const type = getMediaType(data?.name)
  console.log(type)

  if (isLoading) {
    return <Loader loading={!isSuccess} />;
  }
  if (isError) {
    return <>{toastError(error?.message)}</>;
  }

  //TODO: Разбить на отдельные компоненты, чтобы не городить вот это вот всё
  return (
    <div className={styles.container}>
      <div className={styles.container_description}>
        <div className={styles.container_description_name}>
          <label>Название:&nbsp;</label>
          <span>{data?.name}</span>
        </div>
        <div className={styles.container_description_name}>
          <label>Тэги:&nbsp;</label>
          <span>{data?.tags ? data?.tags?.join(", ") : 'Не указано'}</span>
        </div>
        <div className={styles.container_description_name}>
          <label>Длина:&nbsp;</label>
          <span>{data?.length}</span>
        </div>
        <div className={styles.container_description_name}>
          <label>Размер:&nbsp;</label>
          <span>{checkSize(data?.size)}</span>
        </div>
        <div className={styles.container_description_name}>
          <label>Тип:&nbsp;</label>
          <span>{type}</span>
        </div>
        <div className={styles.container_description_name}>
          <label>Hash:&nbsp;</label>
          <span style={{wordBreak: 'break-all'}}>{data?.hash.concat_hash}</span>
        </div>
      </div>
      <div className={styles.container_file}>
        {type === 'image' && (
            <Image
                src={data?.url}
                loading="lazy"

            />
        )}
        {type === 'video' && (
            <video
                src={data?.url}
                controls={true}
            />
        )}
        {type === 'audio' && (
            <audio
                src={data?.url}
                controls
                autoPlay={false}
            />
        )}
      </div>
    </div>
  );
}


//name, tags, length, size, type, hash, file