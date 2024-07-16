import FilesListClientPage from "./FilesListClientPage";

import { FilesService } from "@/src/services/files";
import { FilesListResponse } from "@/src/types/interface/files.interface";

export async function generateMetadata() {
  try {
    const response = await FilesService.getAll();

    if (response) {
      return {
        title: `Файлы ${response.count} штук(-и)`,
        description: `Просмотр списка файлов ${response.count} штук(-и)`,
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
  const data: FilesListResponse = await FilesService.getAll();

  return <FilesListClientPage data={data} />;
}
