import nomenclaturesService from "@/src/services/nomenclatures/nomenclatures.service";

export async function generateMetadata() {
  try {
    const response = await nomenclaturesService.getAll();

    if (response) {
      return {
        title: `Номенклатуры ${response.data.count} штук(-и)`,
        description: `Просмотр списка номенклатур ${response.data.count} штук(-и)`,
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
