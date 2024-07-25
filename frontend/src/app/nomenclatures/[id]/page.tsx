import { Metadata } from "next";

import ListPage from "./ListPage";

import nomenclaturesService from "@/src/services/nomenclatures/nomenclatures.service";

export async function generateMetadata({
  params,
}: {
  params: { id: string };
}): Promise<Metadata> {
  const { id } = params;

  try {
    const response = await nomenclaturesService.getById(id);

    if (response) {
      return {
        title: `${response.data.name}`,
        description: `Просмотр номенклатуры ${response.data.id}`,
      };
    }
  } catch (error) {
    console.error("Failed to fetch metadata:", error);
  }

  return {
    title: "Ошибка получения номенклатуры",
    description: "От сервера не было ответа. Повторите попытку позже.",
  };
}

export default async function Page({ params }: { params: { id: string } }) {
  const idS = params.id.toString();

  return <ListPage id={idS} />;
}
