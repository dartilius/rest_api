import { Metadata } from "next";
import { fetchFilesList } from "@/services/FilesService";
import Card from "@/app/files/components/Card/Card";
import { Pagination } from "@/app/files/components/Pagination";

export const metadata: Metadata = {
    title: "Файлы",
    description: "Список файлов",
};

type FilesListProps = {
    page?: number | string;
    limit?: number | string;
    name?: string;
    file_type?: string;
    tags?: string;
};

export default async function Page(props: { searchParams?: Promise<FilesListProps> }) {
    const searchParams = await props.searchParams;
    const name = searchParams?.name || "";
    const currentPage = Number(searchParams?.page) || 1;
    const limit = Number(searchParams?.limit) || 12;
    const fileType = searchParams?.file_type || "";
    const tags = searchParams?.tags || "";

    const listFiles = await fetchFilesList({ page: currentPage, limit, name });
    const dataFiles = typeof listFiles !== "string" ? listFiles.results : [];
    const countFiles = typeof listFiles !== "string" ? listFiles.count : 0;
    console.log(dataFiles)

    return (
        <>
            <div>
                <Card data={dataFiles}/>
            </div>
            <Pagination currentPage={currentPage} totalPages={Math.ceil(countFiles / limit)} />
        </>
    );
}
