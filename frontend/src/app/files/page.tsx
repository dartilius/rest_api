import { Metadata } from 'next'
import TableListFiles from '@/app/files/components/TableListFile/TableListFiles'
import { getFilesList } from './api'
import { Box } from '@mui/material'

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
	const { page = 1, limit = 10, name = '', file_type = '', tags = [] } = (await searchParams) ?? {}

	const listFiles = await getFilesList({ page, limit, name, file_type, tags })
	const dataFiles = listFiles.results ? listFiles.results : []
	const countFiles = listFiles.count ? listFiles.count : 0
	return (
		<div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', height: '100%' }}>
			<TableListFiles
				data={dataFiles}
				count={countFiles}
				limit={limit}
				page={page}
			/>
		</div>
	)
}

export default FilesListPage
