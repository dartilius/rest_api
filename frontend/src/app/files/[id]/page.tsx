import { getFileDetail } from '@/services/FilesService'
import FileDetails from '@/app/files/[id]/components/FileDetails'
import Head from "next/head";
import {Metadata} from "next";

interface Props {
	params: {
		id: string
	}
}

export async function generateMetadata(
    { params }: Props
): Promise<Metadata> {
    const { id } = params;

    try {
        const fileDetail = await getFileDetail(id);

        // Возвращаем мета-данные на основе данных файла
        return {
            title: fileDetail ? `Файл ${fileDetail.name}` : "Ошибка загрузки файла",
            openGraph: {
                title: fileDetail ? `Файл ${fileDetail.name}` : "Ошибка загрузки файла",
            },
        };
    } catch (error) {
        // В случае ошибки возвращаем дефолтные мета-данные
        console.error("Error loading file details:", error);
        return {
            title: "Ошибка загрузки файла",
            openGraph: {
                title: "Ошибка загрузки файла",
            },
        };
    }
}

const FileDetail = async ({ params }: Props) => {
	// Явное ожидание параметров
	const { id } = await new Promise<{ id: string }>((resolve) => resolve(params))

	try {
		const fileDetail = await getFileDetail(id)

		return (
			<>
				<Head>
					<title>{`Файл ${fileDetail.name}`}</title>
				</Head>
				<div className='container mx-auto p-4'>
					<h1 className='text-3xl font-bold mb-6'>Детали Файла</h1>
					<FileDetails
						data={fileDetail}
						className='mb-6'
					/>
				</div>
			</>
		)
	} catch (error) {
		console.error('Error loading order details:', error)
		return <div className='container mx-auto p-4 text-red-500'>Ошибка загрузки деталей файла</div>
	}
}

export default FileDetail
