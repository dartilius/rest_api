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
		cell: (info) => (
			<Link
				className='flex justify-center'
				href={`/files/${info.getValue()}`}
			>
				{info.getValue()}
			</Link>
		),
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
