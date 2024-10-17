"use client";

import { useParams } from "next/navigation";

import { toastError } from "@/src/utils/toast-error";
import Loader from "@/src/components/ui/Loader";
import useFileQuery, {useDeleteFileQuery} from "@/src/hooks/files/useFileQuery";
import {getMediaType} from "@/src/types/types/getMediaType";

import styles from './FileDesc.module.scss'
import {checkSize} from "@/src/types/types/checkSize";
import {Button, Image} from "@nextui-org/react";
import React, {useState} from "react";
import EditingFileModal from "@/src/app/files/[id]/create/EditingFileModal";
import DeletingModal from "@/src/components/ui/DeletingModal";

export default function ReadFile() {
  const router = useParams();
  const id = router?.id;
  const { data, error, isError, isLoading, isSuccess } = useFileQuery(
    id.toString(),
  );
  const [openCreatingModal, setOpenCreatingModal] = useState<boolean>(false);
  const [openDeletingModal, setOpenDeletingModal] = useState<boolean>(false);
  const deleteFile = useDeleteFileQuery()


  const type = getMediaType(data?.name)

  if (isLoading) {
    return <Loader loading={!isSuccess} />;
  }
  if (isError) {
    return <>{toastError(error?.message)}</>;
  }

  const handleCloseDeletingModal = () => {
    setOpenDeletingModal(false);
  };

  const handleDeletePlaylist = () => {
    deleteFile.mutate(id?.toString())
  }

  return (
    <div className={styles.container}>
      <div className={styles.container_description}>
        <div className={styles.container_description_name}>
          <label>Название:&nbsp;</label>
          <span>{data?.name}</span>
        </div>
        <div className={styles.container_description_name}>
          <label>Тэги:&nbsp;</label>
          <span>{data?.tags ? data?.tags?.map((v: any) => v.name).join(", ") : 'Не указано'}</span>
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
        <div className={styles.container_description_buttons}>
          <Button onClick={() => setOpenCreatingModal(true)}>Edit</Button>
          <Button color="danger" onClick={() => setOpenDeletingModal(true)}>Delete</Button>
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
      <EditingFileModal
          open={openCreatingModal}
          close={() => setOpenCreatingModal(false)}
          tags={data?.tags}
          id={id.toString()}
      />
      <DeletingModal
          close={handleCloseDeletingModal}
          deleteProp={handleDeletePlaylist}
          open={openDeletingModal}
      />
    </div>
  );
}


//name, tags, length, size, type, hash, file