"use client";

import { ChangeEvent, useEffect, useState } from "react";
import { Select, SelectItem } from "@nextui-org/select";
import { Input } from "@nextui-org/input";
import { Button } from "@nextui-org/button";
import { toastSuccess } from "@/src/utils/toast-success";
import { fileTypes } from "@/src/types/types/fileTypes";
import {useCreateFileQuery} from "@/src/hooks/files/useFileQuery";
import {Modal, ModalBody, ModalContent, ModalHeader} from "@nextui-org/react";


type Props = {
  open: boolean;
  close: () => void;
};

export default function FilesCreate(props: Props) {
  const { open, close } = props;
  const [fileType, setFileType] = useState<string>("1");
  const [file, setFile] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const createFile = useCreateFileQuery();

  const getFileMimeType = (fileName: string) => {
    const extension = fileName.split(".").pop();

    switch (extension) {
      case "mp3":
        return "mp3";
      case "wav":
        return "wav";
      case "png":
        return "png";
      case "jpg":
      case "jpeg":
        return "jpeg";
      case "gif":
        return "gif";
      case "pdf":
        return "application/pdf";
      default:
        return "application/octet-stream";
    }
  };
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];

    if (selectedFile) {
      const reader = new FileReader();

      reader.onloadend = () => {
        const base64Data = reader.result as string;
        const mimeType = getFileMimeType(selectedFile.name);

        const base64String = `data:${selectedFile.name}/${mimeType};base64,${base64Data.split(",")[1]}`;

        setFile(base64String);
      };
      reader.readAsDataURL(selectedFile);
    } else {
      setFile(null);
    }
  };

  const handleCreateFile = async () => {
    if (!file) {
      setError("Пожалуйста, выберите файл");

      return;
    }

    createFile.mutate({file_type: Number(fileType), source: file, name: '1', tags: ['msuic']})
    setFile(null);
    setError(null);
  };

  const handleTypeChange = (type: string) => {
    setFileType(type);
  };

  return (
    <div>
      <Modal isOpen={open} onClose={close}>
        <ModalContent>
          <ModalHeader>Создание файла</ModalHeader>
          <ModalBody>
            <form
                className="flex gap-4 flex-col"
                onSubmit={(e) => {
                  e.preventDefault();
                  handleCreateFile();
                }}
            >
              <div>
                <Select
                    defaultSelectedKeys={[`${fileType}`]}
                    label="Выберите тип файла"
                    onChange={(e) => handleTypeChange(e.target.value)}
                >
                  {fileTypes.map((option) => (
                      <SelectItem key={option.key} value={option.key}>
                        {option.label}
                      </SelectItem>
                  ))}
                </Select>
              </div>
              <div>
                {/* <Button style={{ width: "100%" }}> */}
                <Input
                    // className={styles.file}
                    label="Выберите файл"
                    placeholder="Выберите файл"
                    type="file"
                    onChange={handleFileChange}
                />
                {/* </Button> */}
              </div>
              <Button color="secondary" type="submit">
                Создать файл
              </Button>
            </form>
            {error && <p style={{ color: "red" }}>{error}</p>}
          </ModalBody>
        </ModalContent>
      </Modal>
    </div>
  );
}
