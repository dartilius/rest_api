import { convertStatus } from '@/types/checkStatus'
import { INomenclatureStatusHistoryResponse } from '@/types/nomeclaturesType'
import { createColumnHelper } from '@tanstack/react-table'

const columnHelper = createColumnHelper<INomenclatureStatusHistoryResponse>()

export const HistoryStatisticsColumnsTable = [
	columnHelper.accessor('change_time', {
		header: () => <span>Время изменения</span>,
		cell: (info) => <div className='flex justify-center'>{info.getValue()}</div>,
		// footer: (info) => info.column.id,
		enableSorting: true,
	}),
	columnHelper.accessor('status', {
		id: 'status',
		cell: (info) => <i className='flex justify-center'>{convertStatus(info.getValue())}</i>,
		header: () => <span>Статус</span>,
		// footer: (info) => info.column.id,
		enableSorting: true,
	}),
]
