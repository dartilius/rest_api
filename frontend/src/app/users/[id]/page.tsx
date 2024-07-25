import UserClientPage from "./UserPage";

import { UserInfo } from "@/src/types/interface/user.interface";
import { UsersService } from "@/src/services/users/users.service";

type Props = {
  params: { id: string };
};

export async function generateMetadata({ params }: Props) {
  try {
    const response = await UsersService.getById(params.id);

    if (response) {
      return {
        title: `
          Пользователь -
          ${response.fullName.firstName}
          ${response.fullName.lastName} ${response.fullName.middleName ? " " + response.fullName.middleName : ""}`,
        email: response.email,
      };
    }
  } catch (error) {
    console.error("Failed to fetch metadata:", error);
  }

  return {
    title: "Ошибка",
    email: "Ошибка загрузки данных",
  };
}

export default async function NomenclaturePage({ params }: Props) {
  const data: UserInfo | undefined = await UsersService.getById(params.id);

  return <UserClientPage data={data} id={params.id} />;
}
