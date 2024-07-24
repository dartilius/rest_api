import FilesListClientPage from "./FilesListClientPage";

import filesService from "@/src/services/files/files.service";
import { FilesListResponse } from "@/src/types/interface/files.interface";

export async function generateMetadata() {
  try {
    const response = await filesService.getAll();

    if (response) {
      return {
        title: `Файлы ${response.data.count} штук(-и)`,
        description: `Просмотр списка файлов ${response.data.count} штук(-и)`,
      };
    }
  } catch (error) {
    console.error("Failed to fetch metadata:", error);
  }

  return {
    title: "Default List Title",
    description: "Default List Description",
  };
}

export default async function ListPage() {
  const data = await filesService.getAll();

  return <FilesListClientPage data={data.data} />;
}
