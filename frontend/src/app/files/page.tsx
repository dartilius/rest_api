import FilesListClientPage from "./FilesListClientPage";

// import filesService from "@/src/services/files/files.service";

// export async function generateMetadata() {
//   const page = 1;
//   const limit = 10;

//   try {
//     const response = await filesService.getAll({ page, limit });

//     if (response) {
//       return {
//         title: `Файлы ${response.data.count} штук(-и)`,
//         description: `Просмотр списка файлов ${response.data.count} штук(-и)`,
//       };
//     }
//   } catch (error) {
//     console.error("Failed to fetch metadata:", error);
//   }

//   return {
//     title: "Default List Title",
//     description: "Default List Description",
//   };
// }

export default async function ListPage() {
  return <FilesListClientPage />;
}
