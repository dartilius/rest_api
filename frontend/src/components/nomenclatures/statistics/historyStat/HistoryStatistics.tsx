'use client'

import { getNomenclatureStatistics } from '@/app/nomenclatures/api'
import {
	getCoreRowModel,
	getSortedRowModel,
	useReactTable,
	flexRender,
} from '@tanstack/react-table'
import { useState, useEffect } from 'react'
import { INomenclatureStatusHistoryResponse } from '@/types/nomeclaturesType'
import { HistoryStatisticsColumnsTable } from './HistoryStatisticsColumnsTable'

export default function HistoryStatistics({ id, className }: { id: string; className?: string }) {
	const [statistics, setStatistics] = useState<INomenclatureStatusHistoryResponse[]>([])
	const [isLoading, setIsLoading] = useState(true)

	useEffect(() => {
		const fetchStatistics = async () => {
			try {
				setIsLoading(true)
				const res = await getNomenclatureStatistics(id)
				setStatistics(res)
			} catch (error) {
				console.error('Error fetching statistics:', error)
			} finally {
				setIsLoading(false)
			}
		}
		fetchStatistics()
	}, [id])

	const table = useReactTable<INomenclatureStatusHistoryResponse>({
		data: statistics,
		columns: HistoryStatisticsColumnsTable,
		getCoreRowModel: getCoreRowModel(),
		getSortedRowModel: getSortedRowModel(),
		enableSorting: true,
	})

	return (
		<div
			className={`bg-gradient-to-r from-fuchsia-600 to-pink-500 rounded-lg shadow h-full overflow-hidden ${className}`}
		>
			<div className='max-h-[400px] overflow-auto'>
				{isLoading ? (
					<div className='flex items-center justify-center h-32'>
						<div className='animate-spin rounded-full h-8 w-8 border-b-2 border-white'></div>
					</div>
				) : (
					<table className='w-full'>
						<thead className='sticky top-0 bg-fuchsia-700'>
							{table.getHeaderGroups().map((headerGroup) => (
								<tr
									key={headerGroup.id}
									className='h-10 border-b border-slate-300'
								>
									{headerGroup.headers.map((header) => (
										<th
											key={header.id}
											className='px-4 py-2 text-white text-sm font-medium'
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
									className='border-b border-slate-200'
								>
									{row.getVisibleCells().map((cell) => (
										<td
											key={cell.id}
											className='px-4 py-2'
										>
											{flexRender(cell.column.columnDef.cell, cell.getContext())}
										</td>
									))}
								</tr>
							))}
						</tbody>
					</table>
				)}
			</div>
		</div>
	)
}
