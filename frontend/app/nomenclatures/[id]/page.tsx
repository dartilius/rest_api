import NomenclatureClientPage from "./NomenclaturePage";

import { NomenclaturesService } from "@/services/nomenclatures/nomenclatures.service";
import { NomenclatureInterface } from "@/types/interface/nomenclature.interface";

type Props = {
  params: { id: string };
};

export async function generateMetadata({ params }: Props) {
  try {
    const response = await NomenclaturesService.getById(params.id);

    if (response) {
      return {
        title: response.name,
        description: response.description,
      };
    }
  } catch (error) {
    console.error("Failed to fetch metadata:", error);
  }

  return {
    title: "Ошибка",
    description: "Ошибка загрузки данных",
  };
}

export default async function NomenclaturePage({ params }: Props) {
  const data: NomenclatureInterface | undefined =
    await NomenclaturesService.getById(params.id);

  return <NomenclatureClientPage data={data} id={params.id} />;
}
