'use client'

import { useStore } from '@/providers/mobx-provider/MobxProvider'
import { IAdData, IDataAdResponse } from '@/types/orderTypes'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import {
	flexRender,
	getCoreRowModel,
	getSortedRowModel,
	useReactTable,
} from '@tanstack/react-table'
import { observer } from 'mobx-react'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import FiltersPanel from '../filters/FiltersPanel'
import AppBar from '@mui/material/AppBar'
import { Typography } from '@mui/material'
import { adColumnsTable } from './adColumnsTable'
import CreateAdOrderModal from './CreateAdOrderModal'

interface IProps {
	dataResponse: IDataAdResponse
}
const AdOrders = ({ ...props }: IProps) => {
	const { dataResponse } = props
console.log(props);

	const { ordersStore } = useStore()
	const [data, setData] = useState<IAdData[]>([])
	const router = useRouter()
	const pathname = usePathname()
	const searchParams = useSearchParams()
	const { totalPagesAd } = ordersStore
	const page = searchParams.get('page')

	const isNextButtonDisabled = Number(page) >= totalPagesAd

	useEffect(() => {
		const params = new URLSearchParams(searchParams)
		if (!params.has('page')) {
			params.set('page', '1')
			router.replace(`${pathname}?${params.toString()}`)
		}

		setData(dataResponse.results)
		ordersStore.setTotalCountAd(dataResponse.count)
		ordersStore.setActiveTabs(1)
	}, [])

	const table = useReactTable({
		data,
		columns: adColumnsTable,
		getCoreRowModel: getCoreRowModel(),
		getSortedRowModel: getSortedRowModel(),
		enableSorting: true,
	})
	const handleRowClick = (id: string) => {
		// Переход на страницу с расшифровкой
		router.push(`adorders/${id}`)
	}
	const goToPage = (newPage: number) => {
		// ordersStore.setPage(newPage)
		const params = new URLSearchParams(searchParams)
		params.set('page', newPage.toString())
		router.push(`${pathname}?${params.toString()}`)
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
				>
					<Box width={'20%'}>
						<Typography
							noWrap
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
							Рекламные
						</Typography>
					</Box>

					<FiltersPanel />
					<CreateAdOrderModal />
				</Box>
			</AppBar>
			<div className='p-2 w-full overflow-auto'>
				{data.length < 1 ? (
					<p>loading</p>
				) : (
					<table className='w-full'>
						<thead>
							{table.getHeaderGroups().map((headerGroup) => (
								<tr
									key={headerGroup.id}
									className='h-16 border-2 border-slate-300'
								>
									{headerGroup.headers.map((header) => (
										<th
											key={header.id}
											style={{
												width: header.id === 'status' ? '160px' : 'auto',
											}}
										>
											{header.isPlaceholder ? null : (
												<div
													className='cursor-pointer'
													{...{
														onClick: header.column.getToggleSortingHandler(),
													}}
												>
													{flexRender(header.column.columnDef.header, header.getContext())}
													{/* Индикатор сортировки */}
													<span>
														{header.column.getIsSorted()
															? header.column.getIsSorted() === 'asc'
																? ' 🔼'
																: ' 🔽'
															: ''}
													</span>
												</div>
											)}
										</th>
									))}
								</tr>
							))}
						</thead>
						<tbody>
							{table.getRowModel().rows.map((row) => (
								<tr
									key={row.id}
									className='border-2 border-slate-300 text-center h-16'
									onClick={() => handleRowClick(row.original.id)}
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
							{table.getFooterGroups().map((footerGroup) => (
								<tr key={footerGroup.id}>
									{footerGroup.headers.map((header) => (
										<th key={header.id}>
											{header.isPlaceholder
												? null
												: flexRender(header.column.columnDef.footer, header.getContext())}
										</th>
									))}
								</tr>
							))}
						</tfoot>
					</table>
				)}
				<div className='w-full flex items-center justify-center gap-2 p-4'>
					<button
						onClick={() => goToPage(Number(page) - 1)}
						disabled={Number(page) === 1}
						className='px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300'
					>
						Предыдущая
					</button>
					<span>
						Страница: {Number(page)} из {totalPagesAd}
					</span>
					<button
						onClick={() => goToPage(Number(page) + 1)}
						disabled={isNextButtonDisabled}
						className='px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300'
					>
						Следующая
					</button>
				</div>
			</div>
		</Paper>
	)
}

export default observer(AdOrders)
