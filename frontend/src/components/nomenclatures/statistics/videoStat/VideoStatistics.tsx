'use client'

import { getNomenclatureVideoStatistics } from '@/app/nomenclatures/api'
import {
	getCoreRowModel,
	getSortedRowModel,
	useReactTable,
	flexRender,
} from '@tanstack/react-table'
import { useState, useEffect, useRef } from 'react'
import { INomenclatureStatistics } from '@/types/nomeclaturesType'
import { StatisticsColumnsTable } from '../StatisticsColumnsTable'

export default function VideoStatistics({ id, className }: { id: string; className?: string }) {
	const [statistics, setStatistics] = useState<INomenclatureStatistics[]>([])
	const [isLoading, setIsLoading] = useState(false)
	const [page, setPage] = useState(1)
	const [hasMore, setHasMore] = useState(true)
	const containerRef = useRef<HTMLDivElement>(null)

	// Загрузка данных
	const loadData = async (pageNum: number) => {
		try {
			setIsLoading(true)
			const res = await getNomenclatureVideoStatistics(id, pageNum)

			if (pageNum === 1) {
				setStatistics(res.results)
			} else {
				setStatistics((prev) => [...prev, ...res.results])
			}

			setHasMore(!!res.next)
		} catch (error) {
			console.error('Error fetching statistics:', error)
		} finally {
			setIsLoading(false)
		}
	}

	// Первоначальная загрузка при монтировании или изменении id
	useEffect(() => {
		setPage(1)
		setStatistics([])
		setHasMore(true)
		loadData(1)
	}, [id])

	// Обработчик скролла
	const handleScroll = () => {
		const container = containerRef.current
		if (!container || isLoading || !hasMore) return

		const { scrollTop, scrollHeight, clientHeight } = container
		if (scrollHeight - scrollTop <= clientHeight * 1.5) {
			const nextPage = page + 1
			setPage(nextPage)
			loadData(nextPage)
		}
	}

	// Подписка на событие скролла
	useEffect(() => {
		const container = containerRef.current
		if (!container) return

		container.addEventListener('scroll', handleScroll)
		return () => container.removeEventListener('scroll', handleScroll)
	}, [page, isLoading, hasMore])

	const table = useReactTable<INomenclatureStatistics>({
		data: statistics,
		columns: StatisticsColumnsTable,
		getCoreRowModel: getCoreRowModel(),
		getSortedRowModel: getSortedRowModel(),
		enableSorting: true,
	})

	return (
		<div
			className={`bg-gradient-to-r from-fuchsia-600 to-pink-500 rounded-lg shadow h-full overflow-hidden ${className}`}
		>
			<div
				ref={containerRef}
				className='max-h-[400px] overflow-auto'
			>
				<table className='w-full min-w-[640px]'>
					<thead className='sticky top-0 bg-fuchsia-700'>
						{table.getHeaderGroups().map((headerGroup) => (
							<tr
								key={headerGroup.id}
								className='h-10 border-b border-slate-300'
							>
								{headerGroup.headers.map((header) => (
									<th
										key={header.id}
										className='px-2 sm:px-4 py-2 text-white text-xs sm:text-sm font-medium'
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
						{statistics.length < 1 ? (
							<tr>
								<td
									colSpan={3}
									className='text-center py-4 text-white/80'
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
				{isLoading && (
					<div className='flex items-center justify-center h-16'>
						<div className='animate-spin rounded-full h-6 w-6 border-b-2 border-white'></div>
					</div>
				)}
			</div>
		</div>
	)
}
