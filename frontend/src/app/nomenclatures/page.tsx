import NomenclatureListClientPage from "./NomenclatureListClientPage";

import { NomenclatureListResponseInterface } from "@/src/types/interface/nomenclature.interface";
import { NomenclaturesService } from "@/src/services/nomenclatures/nomenclatures.service";

export async function generateMetadata() {
  try {
    const response = await NomenclaturesService.getAll();

    if (response) {
      return {
        title: `Номенклатуры ${response.count} штук(-и)`,
        description: `Просмотр списка номенклатур ${response.count} штук(-и)`,
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
  const data: NomenclatureListResponseInterface =
    await NomenclaturesService.getAll();

  return <NomenclatureListClientPage data={data} />;
}
