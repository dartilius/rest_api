import { Metadata } from "next";
import {getFilesList} from "@/services/FilesService";
import TableListFiles from "@/app/files/components/TableListFile/TableListFiles";
import { Pagination } from "@/app/files/components/Pagination";
import {ModalAddFile} from "@/app/files/components/ModalAddFile/ModalAddFile";
import {Search} from "@/app/nomenclatures/components";
import SelectType from "@/app/files/components/SelectType/SelectType";
import SelectTagsFilterWrapper from "@/app/files/components/SelectTags/SelectTagsFilterWrapper";

export const metadata: Metadata = {
    title: "Файлы",
    description: "Список файлов",
};

const FilesListPage = async ({ searchParams}: {
    searchParams?: {
        page: number
        limit: number
        name: string
        file_type: string
        tags: string[]
    }
}) => {
    const {
        page = 1,
        limit = 20,
        name = '',
        file_type = '',
        tags = [],
    } = (await searchParams) ?? {}

    const listFiles = await getFilesList({ page, limit, name, file_type, tags });
    const dataFiles = listFiles.results ? listFiles.results : [];
    const countFiles = listFiles.count ? listFiles.count : 0;
    return (
        <>
            <div>
                <div
                    style={{
                        display: "grid",
                        gridTemplateColumns: 'repeat(4, 1fr)', // 4 колонки с равной шириной
                        gap: '.5rem',
                        width: '100%',
                        paddingBottom: '12px',
                    }}
                >
                    <div style={{ display: 'flex', justifyContent: 'center' }}>
                        <ModalAddFile />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'center' }}>
                        <Search nameQueryParams='name' label='Название' />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'center' }}>
                        <SelectTagsFilterWrapper />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'center' }}>
                        <SelectType />
                    </div>
                </div>
                <TableListFiles data={dataFiles} />
            </div>
            <Pagination currentPage={page} totalPages={Math.ceil(countFiles / limit)} />
        </>
    );

}

export default FilesListPage;