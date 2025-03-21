import {Metadata} from "next";
import {List} from "@/app/files/componetns/List";
import {fetchFilesList} from "@/services/FilesService";
import {ModalWrapper} from "@/app/files/componetns/Modal";
import SearchForm from "@/app/files/componetns/SearchForm";

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

    const listFiles = await fetchFilesList({page: currentPage,limit, name})
    const dataFiles =  typeof listFiles !== 'string' ? listFiles.results : []
    const countFiles =  typeof listFiles !== 'string' ? listFiles.count : 0
    return (
        <div>
            <ModalWrapper />
            <SearchForm />

            <List limit={limit} currentPage={currentPage} data={dataFiles} count={countFiles}/>
        </div>
    );
}