export const dynamic = 'force-dynamic';

import GroupsListClientPage from "./GroupsListClientPage";

import groupsService from "@/src/services/groups/groups.service";

export async function generateMetadata() {
  const page = 1;
  const limit = 10;

  try {
    const response = await groupsService.getAll({
      page,
      limit,
    });

    if (response) {
      return {
        title: `Группы ${response.data.count} штук(-и)`,
        description: `Просмотр списка групп ${response.data.count} штук(-и)`,
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
  return <GroupsListClientPage />;
}
