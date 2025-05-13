import { INomenclatureMusicStatistics } from '@/types/nomeclaturesType'
import { createColumnHelper } from '@tanstack/react-table'
import Link from 'next/link'

const columnHelper = createColumnHelper<INomenclatureMusicStatistics>()

const formatTime = (seconds: number): string => {
	const minutes = Math.floor(seconds / 60)
	const remainingSeconds = seconds % 60
	return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

export const MusicStatisticsColumnsTable = [
	columnHelper.accessor('file', {
		header: () => <span>Файл</span>,
		cell: (info) => {
			const fileName = info.getValue()
			return (
				<Link
					className='block max-w-[120px] truncate sm:max-w-none sm:truncate-none sm:flex sm:justify-center mx-auto hover:text-blue-200'
					href={`/files/${fileName}`}
					title={fileName}
				>
					{fileName}
				</Link>
			)
		},
		// footer: (info) => info.column.id,
		enableSorting: true,
	}),
	columnHelper.accessor('played', {
		id: 'status',
		cell: (info) => <i className='flex justify-center'>{info.getValue()}</i>,
		header: () => <span>Время проигрывания</span>,
		// footer: (info) => info.column.id,
		enableSorting: true,
	}),
	columnHelper.accessor('length', {
		header: () => <span>Длина файла</span>,
		cell: (info) => <div className='flex justify-center'>{formatTime(info.getValue())}</div>,
		// footer: (info) => info.column.id,
		enableSorting: true,
	}),
]
