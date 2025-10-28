'use client'

import { Box, Theme, useMediaQuery } from '@mui/material'
import CustomPagination from '../Ui/Pagination/CustomPagination'

import { IFilesListResponse } from '@/types/fileTypes'
import { useRef } from 'react'
import MobileView from './Mobile/MobileView'
import { FileTable } from './Table/FileTable'

type Props = {
	data: IFilesListResponse['results']
	count: number
}

export function PageWrapper(props: Props) {
	const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down('md'))
	const topRef = useRef<HTMLDivElement>(null)

	const { data, count } = props

	return (
		<Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
			{isMobile ? (
				<MobileView
					data={data}
					topRef={topRef}
				/>
			) : (
				<FileTable
					data={data}
					countFiles={count}
				/>
			)}

			<CustomPagination
				totalItems={count}
				topRef={topRef}
			/>
		</Box>
	)
}
