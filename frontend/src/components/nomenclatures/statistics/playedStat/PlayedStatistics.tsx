'use client'

import { getNomenclaturePlayedStatistics } from '@/app/nomenclatures/api'
import { useNotification } from '@/hooks/useNotification'
import { INomenclatureStatistics } from '@/types/nomeclaturesType'
import {
	flexRender,
	getCoreRowModel,
	getSortedRowModel,
	useReactTable,
} from '@tanstack/react-table'
import { useEffect, useRef, useState } from 'react'
import { StatisticsColumnsTable } from '../StatisticsColumnsTable'

export function PlayedStatistics({
	id,
	type,
	className,
}: {
	id: string
	type: string
	className?: string
}) {
	const [statistics, setStatistics] = useState<INomenclatureStatistics[]>([])
	const [isLoading, setIsLoading] = useState(false)
	const [page, setPage] = useState(1)
	const [hasMore, setHasMore] = useState(true)
	const containerRef = useRef<HTMLDivElement>(null)
	const { showNotification } = useNotification()

	const loadData = async (pageNum: number) => {
		try {
			setIsLoading(true)
			const res = await getNomenclaturePlayedStatistics(id, type, pageNum)

			if (pageNum === 1) {
				setStatistics(res.results)
			} else {
				setStatistics((prev) => [...prev, ...res.results])
			}

			setHasMore(!!res.next)
		} catch (error: any) {
			showNotification(error.message, 'error')
			console.error('Error fetching statistics:', error)
		} finally {
			setIsLoading(false)
		}
	}

	useEffect(() => {
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
			className={`bg-gradient-to-r from-blue-900 via-indigo-900 to-blue-800 rounded-lg shadow h-full overflow-hidden ${className}`}
		>
			<div
				ref={containerRef}
				className='max-h-[400px] overflow-auto'
			>
				<table className='w-full min-w-[640px]'>
					<thead className='sticky top-0 bg-blue-900'>
						{table.getHeaderGroups().map((headerGroup) => (
							<tr
								key={headerGroup.id}
								className='h-10 border-b border-blue-700'
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
						{statistics?.length > 0 &&
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
							))}
					</tbody>
				</table>
				{isLoading && (
					<div className='flex items-center justify-center h-16'>
						<div className='animate-spin rounded-full h-6 w-6 border-b-2 border-white'></div>
					</div>
				)}
				{statistics?.length === 0 && !isLoading && (
					<div className='flex items-center justify-center h-16'>
						<div className='text-red-500'>Нет данных</div>
					</div>
				)}
			</div>
		</div>
	)
}
