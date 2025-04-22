import { Metadata } from 'next'
import { getFilesList } from '@/services/FilesService'
import TableListFiles from '@/app/files/components/TableListFile/TableListFiles'

export const metadata: Metadata = {
	title: 'Файлы',
	description: 'Список файлов',
}

const FilesListPage = async ({
	searchParams,
}: {
	searchParams?: {
		page: number
		limit: number
		name: string
		file_type: string
		tags: string[]
	}
}) => {
	const { page = 1, limit = 20, name = '', file_type = '', tags = [] } = (await searchParams) ?? {}

	const listFiles = await getFilesList({ page, limit, name, file_type, tags })
	const dataFiles = listFiles.results ? listFiles.results : []
	const countFiles = listFiles.count ? listFiles.count : 0
	return (
		<div>
			<TableListFiles
				data={dataFiles}
				count={countFiles}
			/>
		</div>
	)
}

export default FilesListPage
