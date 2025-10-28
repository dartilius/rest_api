'use client'

import { getNomenclatureAdStat } from '@/app/nomenclatures/api'
import { INomenclatureAdStatResponse } from '@/types/nomeclaturesType'
import { flexRender, getCoreRowModel, useReactTable } from '@tanstack/react-table'
import { useEffect, useState } from 'react'
import { AdStatisticsColumnsTable } from './AdStatColumnsTable'
import PanelAdStat from './PanelAdStat'

export function AdStat({ id, className }: { id: string; className?: string }) {
	const [adStat, setAdStat] = useState<INomenclatureAdStatResponse[]>([])
	const [isLoading, setIsLoading] = useState(true)
	const [date, setDate] = useState<string>(new Date().toISOString().split('T')[0])

	useEffect(() => {
		const fetchAdStat = async () => {
			try {
				setIsLoading(true)
				const res = await getNomenclatureAdStat(id, date)
				setAdStat(res)
			} catch (error) {
				console.error('Ошибка при запросе статистики номенклатуры:', error)
			} finally {
				setIsLoading(false)
			}
		}
		fetchAdStat()
	}, [id, date])

	const table = useReactTable<INomenclatureAdStatResponse>({
		data: adStat,
		columns: AdStatisticsColumnsTable,
		getCoreRowModel: getCoreRowModel(),
	})

	return (
		<div
			className={`bg-gradient-to-r from-blue-900 via-indigo-900 to-blue-800 rounded-lg shadow h-full overflow-hidden w-full ${className}`}
		>
			<div className='max-h-[400px] overflow-auto w-full'>
				<div className='sticky top-0 w-[640px] md:w-full'>
					<PanelAdStat
						setDate={setDate}
						date={date}
					/>
				</div>
				{isLoading ? (
					<div className='flex items-center justify-center h-32'>
						<div className='animate-spin rounded-full h-8 w-8 border-b-2 border-white'></div>
					</div>
				) : (
					<table className='w-[640px] md:w-full'>
						<thead className='sticky top-[73px] bg-blue-900'>
							{table.getHeaderGroups().map((headerGroup) => (
								<tr
									key={headerGroup.id}
									className='h-10 border-b border-blue-700'
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
						<tbody className='text-sm sm:text-base'>
							{adStat.length < 1 ? (
								<tr>
									<td
										colSpan={4}
										className='text-center py-4 text-red-500 '
									>
										Нет данных
									</td>
								</tr>
							) : (
								table.getRowModel().rows.map((row) => (
									<tr
										key={row.id}
										className='border-b border-slate-200 hover:bg-white/5'
									>
										{row.getVisibleCells().map((cell) => (
											<td
												key={cell.id}
												className='px-2 sm:px-4 py-2 whitespace-nowrap overflow-hidden text-ellipsis'
											>
												{flexRender(cell.column.columnDef.cell, cell.getContext())}
											</td>
										))}
									</tr>
								))
							)}
						</tbody>
					</table>
				)}
			</div>
		</div>
	)
}
