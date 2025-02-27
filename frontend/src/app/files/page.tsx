import {Metadata} from "next";
import {List} from "@/app/files/componetns/List";

export const metadata: Metadata = {
        title: 'Файлы',
        description: 'Список файлов'
}

type FilesListProps = {
    page?: number | string;
    limit?: number | string;
    name?: string;
    file_type?: string;
    tags?: string;
}

export default async function Page(props: {
    searchParams?: Promise<FilesListProps>
}) {
    const searchParams = await props.searchParams
    const name = searchParams?.name || '';
    const currentPage = Number(searchParams?.page) || 1;
    const limit = Number(searchParams?.limit) || 10
    const fileType = searchParams?.file_type || '';
    const tags = searchParams?.tags || '';
    return (
        <List limit={limit} currentPage={currentPage} file_type={fileType} name={name} tags={tags}/>
    );
}