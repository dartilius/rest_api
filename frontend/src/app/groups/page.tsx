import GroupsListClientPage from "./GroupsListClientPage";

import { GroupsService } from "@/src/services/groups/groups.service";
import { GroupsListResponse } from "@/src/types/interface/groups.interface";

export async function generateMetadata() {
  try {
    const response = await GroupsService.getAll();

    if (response) {
      return {
        title: `Группы ${response.count} штук(-и)`,
        description: `Просмотр списка групп ${response.count} штук(-и)`,
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
  const data: GroupsListResponse = await GroupsService.getAll();

  return <GroupsListClientPage data={data} />;
}
