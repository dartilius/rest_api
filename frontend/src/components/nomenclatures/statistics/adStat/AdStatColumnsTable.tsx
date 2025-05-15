import { INomenclatureAdStatResponse } from '@/types/nomeclaturesType'
import { formatTime } from '@/utils'
import { createColumnHelper } from '@tanstack/react-table'

const columnHelper = createColumnHelper<INomenclatureAdStatResponse>()

export const AdStatisticsColumnsTable = [
	columnHelper.accessor('played', {
		header: () => <span>Время проигрования</span>,
		cell: (info) => <div className='flex justify-center'>{info.getValue()}</div>,
		enableSorting: true,
	}),
	columnHelper.accessor('ad_block', {
		id: 'status',
		cell: (info) => <i className='flex justify-center'>{info.getValue()}</i>,
		header: () => <span>Рекламный блок</span>,
		enableSorting: true,
	}),
	columnHelper.accessor('file', {
		header: () => <span>Файл</span>,
		cell: (info) => <div className='flex justify-center'>{info.getValue()}</div>,
		enableSorting: true,
	}),
	columnHelper.accessor('length', {
		header: () => <span>Длина</span>,
		cell: (info) => <div className='flex justify-center'>{formatTime(info.getValue())}</div>,
		enableSorting: true,
	}),
]
