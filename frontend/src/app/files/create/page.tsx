"use client";

import {ChangeEvent, useEffect, useState} from "react";
import {getTokenStorage} from "@/src/services/auth/auth.helper";
import {useTagsQuery} from "@/src/hooks/tags/useTagsQuery";
import {toastError} from "@/src/utils/toast-error";
import {toastSuccess} from "@/src/utils/toast-success";
import filesService from "@/src/services/files/files.service";
import {fileTypes} from "@/src/types/types/fileTypes";
import {Button, Input, Select, SelectItem} from "@nextui-org/react";
import {useGetFileMimeType} from "@/src/hooks/useFileType";

export default function FilesCreate() {
    // const [name, setName] = useState("");
  const [fileType, setFileType] = useState<string>("1");
  const [tags, setTags] = useState<any>([]);
  const [file, setFile] = useState<string | null>(null);
  const [nameTags, setNameTags] = useState("");
  const [selectedTagIds, setSelectedTagIds] = useState<number[]>([]);
  const token = getTokenStorage();

  const {error, isError, data, isSuccess, isLoading} = useTagsQuery()

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];

    if (selectedFile) {
      const reader = new FileReader();

      reader.onloadend = () => {
        const base64Data = reader.result as string;
        const mimeType = useGetFileMimeType(selectedFile.name);

        const base64String = `data:${selectedFile.name};base64,${base64Data.split(",")[1]}`;

        setFile(base64String);
        console.log(file)
      };
      reader.readAsDataURL(selectedFile);
    } else {
      setFile(null);
    }
  };

  const handleCreateFile = async () => {

    try {
      const fileData: any = {
        // name,
        file_type: Number(fileType),
        source: file,
        tags: selectedTagIds,
      };

      const response = await filesService.create(fileData);

      toastSuccess("File created successfully");
      setSelectedTagIds([]);
      setFile(null);
      return response
    } catch (error) {
      toastError(error);
    }
  };

  const handleTagChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const selectedKeys = new Set(
      Array.from(event.target.selectedOptions, (option) => option.value),
    );

    setSelectedTagIds(Array.from(selectedKeys).map(Number));
  };

  const handleTypeChange = (type: string) => {
    setFileType(type);
  };

  const handleCreateTags = async () => {
    const tagsData = { name: nameTags };

    console.log(tagsData);

    try {
      const response = await filesService.create(tagsData);

      console.log("Tags created successfully:", response);
      setNameTags("");
    } catch (error: any) {
      console.error("Error creating tags:", error);
    }
  };

  return (
    <div>
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
          <Select
            multiple
            label="Выберите тэги"
            selectedKeys={new Set(selectedTagIds.map(String))}
            onChange={handleTagChange}
          >
            {tags.map((option: any) => (
              <SelectItem key={option.id} value={String(option.id)}>
                {option.name}
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
      <form
        className="flex gap-4 flex-col"
        onSubmit={(e) => {
          e.preventDefault();
          handleCreateTags();
        }}
      >
        <div>
          <Input
            label="Тег"
            placeholder="Введите название тега"
            type="text"
            value={nameTags}
            onChange={(e) => setNameTags(e.target.value)}
          />
          <Button color="secondary" type="submit">
            Создать тег
          </Button>
        </div>
      </form>
      {/*{error && <p style={{ color: "red" }}>{error}</p>}*/}
    </div>
  );

}
