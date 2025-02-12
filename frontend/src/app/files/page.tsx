// import FilesService from "@/services/FilesService";
// import { IFilesListResponse, IFilesResult } from "@/interfaces/Files.Interface";
// import { Metadata } from "next";
//
// // Функция для получения данных и мета-данных
// export async function getData(): Promise<{ metadata: Metadata; filesList: IFilesResult[] }> {
//     try {
//         const res = await FilesService.getAll({
//             page: 1,
//             limit: 10,
//         });
//         return {
//             filesList: res.results,
//             metadata: {
//                 title: `Файлы ${res.count} штук`,
//                 description: 'Список файлов'
//             }
//         };
//     } catch (err) {
//         console.log(err);
//         // Возвращаем значения по умолчанию в случае ошибки
//         return {
//             filesList: [],
//             metadata: {
//                 title: 'Ошибка загрузки',
//                 description: 'Не удалось загрузить список файлов'
//             }
//         };
//     }
// }
//
// export async function generateMetadata(): Promise<Metadata> {
//     const { metadata } = await getData();
//     return metadata;
// }
//
// export default async function Page() {
//     let files: IFilesResult[] = [];
//     let errorMessage: string | null = null;
//
//     try {
//         const { filesList } = await getData();
//         files = filesList;
//     } catch (error) {
//         if (error instanceof Error) {
//             errorMessage = error.message;
//         } else {
//             errorMessage = "Неизвестная ошибка";
//         }
//     }
//
//     return (
//         <div>
//             <h1>Файлы</h1>
//             {errorMessage ? (
//                 <div>Произошла ошибка: {errorMessage}</div>
//             ) : files?.length > 0 ? (
//                 files.map((file) => (
//                     <div key={file.id}>
//                         {file.name}
//                     </div>
//                 ))
//             ) : (
//                 <div>Нет доступных файлов</div>
//             )}
//         </div>
//     );
// }


import {IFilesListResponse, IFilesResult} from "@/interfaces/Files.Interface";
import FilesFilter from "@/app/files/componetns/FilesFilter";
import ApiRequest from "@/services/ApiRequest";
import FilesService from "@/services/FilesService";
import {lazy, Suspense} from "react";
import {Skeleton} from "@mui/material";
import {API_URL} from "@/config/api.config";
import {cookies} from "next/headers";

const FilesList = lazy(() => {
        console.log("Loading FilesList...");
        return import('@/app/files/componetns/FilesList')
});

export async function getFiles(queryParams: Record<string, string>): Promise<IFilesListResponse> {
    const cookieStore = await cookies();
    const accessToken = cookieStore.get("accessToken")?.value;
    const queryString = new URLSearchParams(queryParams).toString();
    const url = `${process.env.NEXT_PUBLIC_API_URL}/api/files?${queryString}`;

    const res = await fetch(url, {
        cache: "no-store",
        headers: {
            Authorization: `access_token ${accessToken}`,
        }
    });

    if (!res.ok) throw new Error("Ошибка загрузки файлов");
    return res.json(); // Вернется Promise<IFilesListResponse>
}

export default async function Page({searchParams}: { searchParams?: Record<string, string> }) {
    if (!searchParams) {
        throw new Error("no searchParams provided");
    }

    const params = new URLSearchParams(Object.entries(searchParams ?? {}));
    const page = params.get("page") ?? "1";
    const limit = params.get("limit") ?? "100";

    const files = await getFiles({page, limit});

    return (
        <div>
            <FilesFilter/>
            <Suspense fallback={<div>Loading...</div>}>
                <FilesList files={files.results} />
            </Suspense>
        </div>
    );
}