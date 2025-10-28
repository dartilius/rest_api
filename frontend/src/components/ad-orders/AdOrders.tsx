'use client'

import { useStore } from '@/providers/mobx-provider/MobxProvider'
import { IAdData, IDataAdResponse } from '@/types/orderTypes'
import { Theme, Typography, useMediaQuery } from '@mui/material'
import AppBar from '@mui/material/AppBar'
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
import { useEffect, useRef, useState } from 'react'
import FiltersPanel from '../filters/FiltersPanel'
import CustomPagination from '../Ui/Pagination/CustomPagination'
import { adColumnsTable } from './adColumnsTable'
import CreateAdOrderModal from './CreateAdOrderModal'
import MobileAdViewTable from '../Ui/Table/MobileAdTableView'
import DesktopAdTableView from '../Ui/Table/DesktopAdTableView'

interface IProps {
	dataResponse: IDataAdResponse
}
const AdOrders = ({ ...props }: IProps) => {
	const { dataResponse } = props
	console.log(props)
	const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down('md'))
	const { ordersStore } = useStore()
	const [data, setData] = useState<IAdData[]>([])
	const router = useRouter()
	const pathname = usePathname()
	const searchParams = useSearchParams()
	const topRef = useRef<HTMLDivElement>(null)

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
					// zIndex: (theme) => theme.zIndex.drawer + 1,
					top: 0,
					backgroundColor: 'background.paper',
				}}
			>
				{isMobile ? (
					<Box
						display={'flex'}
						justifyContent={'center'}
						alignItems={'center'}
						width={'100%'}
						height={'100%'}
						padding={1}
						gap={1}
					>
						<FiltersPanel />
						<Box
							sx={{
								display: 'flex',
								justifyContent: 'center',
								alignItems: 'center',
								width: '100%',
								height: '100%',
							}}
						>
							<Typography
								noWrap
								component={'span'}
								sx={{
									fontSize: '1.5rem',
									fontStyle: 'oblique',
									textTransform: 'uppercase',
									color: '#152c4d',
								}}
							>
								Рекламные
							</Typography>
						</Box>
						<CreateAdOrderModal />
					</Box>
				) : (
					<Box
						display={'flex'}
						flexDirection={'column'}
						justifyContent={'center'}
						alignItems={'center'}
						width={'100%'}
						height={'100%'}
						padding={1}
						gap={1}
					>
						<Box
							sx={{
								display: 'flex',
								justifyContent: 'center',
								alignItems: 'center',
								width: '100%', // Занимает всю доступную ширину
								height: '100%',
								gap: 2,
							}}
						>
							<Typography
								noWrap
								component={'span'}
								sx={{
									fontSize: '1.5rem',
									fontStyle: 'oblique',
									textTransform: 'uppercase',
									color: '#152c4d',
								}}
							>
								Рекламные
							</Typography>
							<CreateAdOrderModal />
						</Box>

						<FiltersPanel />
					</Box>
				)}
			</AppBar>
			<div
				className='p-2 w-full overflow-auto'
				ref={topRef}
			>
				{data.length < 1 ? (
					<p>Нет данных</p>
				) : 
				
				// (
				// 	<table className='w-full'>
				// 		<thead>
				// 			{table.getHeaderGroups().map((headerGroup) => (
				// 				<tr
				// 					key={headerGroup.id}
				// 					className='h-16 border-2 border-slate-300'
				// 				>
				// 					{headerGroup.headers.map((header) => (
				// 						<th
				// 							key={header.id}
				// 							style={{
				// 								width: header.id === 'status' ? '160px' : 'auto',
				// 							}}
				// 						>
				// 							{header.isPlaceholder ? null : (
				// 								<div
				// 									className='cursor-pointer'
				// 									{...{
				// 										onClick: header.column.getToggleSortingHandler(),
				// 									}}
				// 								>
				// 									{flexRender(header.column.columnDef.header, header.getContext())}
				// 									{/* Индикатор сортировки */}
				// 									<span>
				// 										{header.column.getIsSorted()
				// 											? header.column.getIsSorted() === 'asc'
				// 												? ' 🔼'
				// 												: ' 🔽'
				// 											: ''}
				// 									</span>
				// 								</div>
				// 							)}
				// 						</th>
				// 					))}
				// 				</tr>
				// 			))}
				// 		</thead>
				// 		<tbody>
				// 			{table.getRowModel().rows.map((row) => (
				// 				<tr
				// 					key={row.id}
				// 					className='border-2 border-slate-300 text-center h-16'
				// 					onClick={() => handleRowClick(row.original.id)}
				// 				>
				// 					{row.getVisibleCells().map((cell) => (
				// 						<td
				// 							key={cell.id}
				// 							className='text-center cursor-pointer p-2'
				// 						>
				// 							{flexRender(cell.column.columnDef.cell, cell.getContext())}
				// 						</td>
				// 					))}
				// 				</tr>
				// 			))}
				// 		</tbody>
				// 		<tfoot>
				// 			{table.getFooterGroups().map((footerGroup) => (
				// 				<tr key={footerGroup.id}>
				// 					{footerGroup.headers.map((header) => (
				// 						<th key={header.id}>
				// 							{header.isPlaceholder
				// 								? null
				// 								: flexRender(header.column.columnDef.footer, header.getContext())}
				// 						</th>
				// 					))}
				// 				</tr>
				// 			))}
				// 		</tfoot>
				// 	</table>
				// )
				isMobile ? (
          <MobileAdViewTable data={data} onRowClick={handleRowClick} />
        ) : (
          <DesktopAdTableView data={data} onRowClick={handleRowClick} />
        )}
				{/* } */}
			</div>
			<Box
				sx={{
					flexShrink: 0,
					p: 0,
					display: 'flex',
					justifyContent: 'center',
					backgroundColor: 'background.paper',
				}}
			>
				<CustomPagination
					totalItems={dataResponse.count}
					topRef={topRef}
				/>
			</Box>
		</Paper>
	)
}

export default observer(AdOrders)
