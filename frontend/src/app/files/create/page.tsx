"use client";

import { ChangeEvent, useState } from "react";
import { Select, SelectItem } from "@nextui-org/select";
import { Input } from "@nextui-org/input";
import { Button } from "@nextui-org/button";
import { useCreateFileQuery, useTagsQuery } from "@/src/hooks/files/useFileQuery";
import { Modal, ModalBody, ModalContent, ModalHeader } from "@nextui-org/react";
import { fileTypes } from "@/src/types/types/fileTypes";

type Props = {
  open: boolean;
  close: () => void;
};

export default function FilesCreate(props: Props) {
  const { open, close } = props;
  const [fileType, setFileType] = useState<string>("1");
  const [files, setFiles] = useState<{ file_type: number; source: string; tags: { name: string }[] }[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [tags, setTags] = useState<string[]>([]);
  const [searchTag, setSearchTag] = useState<string>(""); // Новый стейт для поиска тега
  const createFile = useCreateFileQuery();

  const { data: dataTags } = useTagsQuery({ page: 1, limit: 1000 });
  const listTagsName = dataTags?.results.map((tag) => tag.name) || [];

  // Фильтруем теги на основе введенного текста
  const filteredTags = listTagsName.filter((tag) =>
      tag.toLowerCase().includes(searchTag.toLowerCase())
  );

  const handleTagSearchChange = (e: ChangeEvent<HTMLInputElement>) => {
    setSearchTag(e.target.value);
  };

  const handleTagChange = (selectedTags: string[]) => {
    setTags(selectedTags); // Update tags as an array of strings
  };

  const handleAddNewTag = () => {
    if (searchTag && !listTagsName.includes(searchTag) && !tags.includes(searchTag)) {
      setTags((prevTags) => [...prevTags, searchTag]);
      setSearchTag(""); // Очистить поле ввода после добавления тега
    }
  };



  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleAddNewTag(); // Add the tag if Enter key is pressed
      e.preventDefault(); // Prevent form submission on Enter
    }
  };

  const getFileMimeType = (fileName: string) => {
    const extension = fileName.split(".").pop();

    switch (extension) {
      case "mp3":
        return "audio/mp3";
      case "wav":
        return "audio/wav";
      case "png":
        return "image/png";
      case "jpg":
      case "jpeg":
        return "image/jpeg";
      case "gif":
        return "image/gif";
      case "pdf":
        return "application/pdf";
      default:
        return "application/octet-stream";
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (selectedFiles) {
      const fileReaders: FileReader[] = [];
      const newFiles: { file_type: number; source: string; tags: { name: string }[] }[] = [];

      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        const reader = new FileReader();

        reader.onloadend = () => {
          const base64Data = reader.result as string;
          const mimeType = getFileMimeType(file.name);
          const base64String = `data:${file.name};base64,${base64Data.split(",")[1]}`;

          newFiles.push({
            file_type: Number(fileType),
            source: base64String,
            tags: tags.map((tag) => ({ name: tag })), // Конвертируем строки тегов в объекты
          });

          // Проверяем, что все файлы обработаны
          if (newFiles.length === selectedFiles.length) {
            setFiles((prevFiles) => [...prevFiles, ...newFiles]);
          }
        };

        fileReaders.push(reader);
        reader.readAsDataURL(file);
      }
    } else {
      setFiles([]);
    }
  };


  const handleCreateFiles = async () => {
    if (files.length === 0) {
      setError("Пожалуйста, выберите файлы");
      return;
    }

    // Send all files as an array in a single request
    createFile.mutate(files);

    setFiles([]);
    setTags([])
    setSearchTag('')
    setFileType('')
    setError(null);
  };

  const handleTypeChange = (type: string) => {
    setFileType(type);
  };

  return (
      <div>
        <Modal isOpen={open} onClose={close}>
          <ModalContent>
            <ModalHeader>Создание файлов</ModalHeader>
            <ModalBody>
              <form
                  className="flex gap-4 flex-col"
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleCreateFiles();
                  }}
              >
                <div className='flex flex-col gap-2'>
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
                  <div>
                    {/* Input для поиска или добавления тегов */}
                    <Input
                        placeholder="Введите тег для поиска или добавления"
                        value={searchTag}
                        onChange={handleTagSearchChange}
                        onKeyDown={handleKeyDown} // Добавляем новый тег по нажатию Enter
                    />
                  </div>
                </div>
                <div>
                  <Input
                      label="Выберите файлы"
                      placeholder="Выберите файлы"
                      type="file"
                      onChange={handleFileChange}
                      multiple={true}
                  />
                </div>
                <Button color="secondary" type="submit">
                  Создать файлы
                </Button>
              </form>
              {error && <p style={{ color: "red" }}>{error}</p>}
            </ModalBody>
          </ModalContent>
        </Modal>
      </div>
  );
}
