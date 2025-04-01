import { Metadata } from "next";
import {getFilesList} from "@/services/FilesService";
import TableListFiles from "@/app/files/components/TableListFile/TableListFiles";
import { Pagination } from "@/app/files/components/Pagination";
import {ModalAddFile} from "@/app/files/components/ModalAddFile/ModalAddFile";
import {Search} from "@/app/nomenclatures/components";
import SelectType from "@/app/files/components/SelectType/SelectType";

export const metadata: Metadata = {
    title: "Файлы",
    description: "Список файлов",
};

const FilesListPage = async ({ searchParams,}: {
    searchParams?: {
        page: number
        limit: number
        name: string
        file_type: string
    }
}) => {
    const {
        page = 1,
        limit = 20,
        name = '',
        file_type = '',
    } = (await searchParams) ?? {}

    const listFiles = await getFilesList({ page, limit, name, file_type });
    const dataFiles = listFiles.results ? listFiles.results : [];
    const countFiles = listFiles.count ? listFiles.count : 0;
    console.log(dataFiles)

    return (
        <>
            <div>
                <div style={{display: "flex", flexDirection: 'row', justifyContent: 'space-between', gap: '.5rem', width: '100%', paddingBottom: '12px'}}>
                    <ModalAddFile />
                    <div style={{width: '45%'}}>
                        <Search nameQueryParams='name' label='Название' />
                    </div>
                    <SelectType />
                </div>
                <TableListFiles data={dataFiles}/>
            </div>
            <Pagination currentPage={page} totalPages={Math.ceil(countFiles / limit)} />
        </>
    );
}

export default FilesListPage;