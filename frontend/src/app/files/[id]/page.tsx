import {getFileDetail} from "@/services/FilesService";
import FileDetails from "@/app/files/[id]/components/FileDetails";

interface Props {
    params: {
        id: string
    }
}

const FileDetail = async ({ params }: Props) => {
    // Явное ожидание параметров
    const { id } = await new Promise<{id: string}>(resolve =>
        resolve(params)
    )

    try {
        const fileDetail = await getFileDetail(id)

        return (
            <div className='container mx-auto p-4'>
                <h1 className='text-3xl font-bold mb-6'>Детали Файла</h1>
                <FileDetails data={fileDetail} className='mb-6' />
            </div>
        )
    } catch (error) {
        console.error('Error loading order details:', error)
        return (
            <div className='container mx-auto p-4 text-red-500'>
                Ошибка загрузки деталей файла
            </div>
        )
    }
}

export default FileDetail