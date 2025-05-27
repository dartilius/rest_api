'use client'

import FiltersWrapper from '@/app/files/components/FilterWrapper/FiltersWrapper'
import CustomPagination from '@/components/Ui/Pagination/CustomPagination'
import { IFilesListResponse } from '@/types/fileTypes'
import { AppBar, Box, Paper, Typography } from '@mui/material'
import {
	flexRender,
	getCoreRowModel,
	getSortedRowModel,
	useReactTable,
} from '@tanstack/react-table'
import { useRouter } from 'next/navigation'
import { useRef } from 'react'
import { fileColumnsTable } from './fileColumnsTable'

interface IProps {
	data: IFilesListResponse['results']
	countFiles: number
}

export const FileTable = ({ data, countFiles }: IProps) => {
	const { push } = useRouter()

	const topRef = useRef<HTMLDivElement>(null)

	const table = useReactTable({
		data,
		columns: fileColumnsTable,
		getCoreRowModel: getCoreRowModel(),
		getSortedRowModel: getSortedRowModel(),
		enableSorting: true,
	})

	const handleRowClick = (id: string) => {
		push(`files/${id}`)
	}

	return (
		<Paper
			elevation={4}
			sx={{
				width: '100%',
				height: '100%',
				display: 'flex',
				flexDirection: 'column',
			}}
		>
			<AppBar
				position='sticky'
				sx={{
					zIndex: (theme) => theme.zIndex.drawer + 1,
					top: 0,
					backgroundColor: 'background.paper',
				}}
			>
				<Box
					display={'flex'}
					justifyContent={'center'}
					alignItems={'center'}
					width={'100%'}
					padding={1}
					gap={2}
					flexDirection={'column'}
				>
					<Box width={'20%'}>
						<Typography
							variant='h5'
							noWrap
							component='div'
							fontStyle={'uppercase'}
							sx={{
								// flexGrow: 1,
								alignSelf: 'center',
								justifyContent: 'center',
								alignItems: 'center',
								textAlign: 'center',
								fontSize: '2rem',
								fontStyle: 'oblique',
								fontVariantCaps: 'all-small-caps',
								color: '#152c4d',
							}}
						>
							Файлы
						</Typography>
					</Box>
					<FiltersWrapper />
				</Box>
			</AppBar>
			<div className='p-2 w-full flex-1 overflow-auto'>
				{data.length < 1 ? (
					<p>loading</p>
				) : (
					<table className='w-full '>
						<thead>
							{table.getHeaderGroups().map((headerGroup) => (
								<tr
									key={headerGroup.id}
									className='h-16 border-2 border-slate-300'
								>
									{headerGroup.headers.map((header) => (
										<th
											key={header.id}
											className='px-2 sm:px-4 py-2 text-black text-xs sm:text-sm font-medium'
										>
											{header.isPlaceholder
												? null
												: flexRender(header.column.columnDef.header, header.getContext())}
										</th>
									))}
								</tr>
							))}
						</thead>
						<tbody>
							{table.getRowModel().rows.map((row) => (
								<tr
									key={row.id}
									onClick={() => handleRowClick(row.original.id)}
									className='border-2 border-slate-300 text-center h-16'
								>
									{row.getVisibleCells().map((cell) => (
										<td
											key={cell.id}
											className='text-center cursor-pointer p-2'
										>
											{flexRender(cell.column.columnDef.cell, cell.getContext())}
										</td>
									))}
								</tr>
							))}
						</tbody>
						<tfoot>
							<tr>
								<td colSpan={table.getAllColumns().length}>
									<CustomPagination
										totalItems={countFiles}
										topRef={topRef}
									/>
								</td>
							</tr>
						</tfoot>
					</table>
				)}
			</div>
		</Paper>
	)
}
