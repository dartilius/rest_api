import FileDetails from '@/app/files/[id]/components/FileDetails'
import { Metadata, ResolvingMetadata } from 'next'
import Head from 'next/head'
import { getFileDetail } from '../api'

interface Props {
	params: {
		id: string
	}
}

export async function generateMetadata(
	{ params }: Props,
	parent: ResolvingMetadata,
): Promise<Metadata> {
	const { id } = await new Promise<{ id: string }>((resolve) => resolve(params))

	const res = await getFileDetail(id)

	return {
		title: res.name,
		description: res.name,
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
