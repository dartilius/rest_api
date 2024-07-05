"use client";
import React from "react";
import { Select, SelectItem } from "@nextui-org/react";

import { fileTypes } from "../../../types/types/fileTypes";

type FileType = {
  setFileType: any;
  type: string;
};

const FileType = (props: FileType) => {
  const { setFileType, type } = props;
  const handleChange = (value: string) => {
    if (value === "all") {
      setFileType(""); // Сбросить фильтр
    } else {
      const parsedValue = Number(value);

      if (!isNaN(parsedValue)) {
        setFileType(parsedValue);
      } else {
        console.error("Invalid value selected:", value);
      }
    }
  };

  return (
    <Select
      defaultSelectedKeys={[`${type}`]}
      label="Выберите тип файла"
      onChange={(e) => handleChange(e.target.value)}
    >
      {fileTypes.map((option) => (
        <SelectItem key={option.key} value={option.key}>
          {option.label}
        </SelectItem>
      ))}
    </Select>
  );
};

export default FileType;
