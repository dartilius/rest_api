import { convertStatus } from '@/types/checkStatus'
import { INomenclatures } from '@/types/nomeclaturesType'
import { getStatusColor } from '@/utils'
import { createColumnHelper } from '@tanstack/react-table'

const columnHelper = createColumnHelper<INomenclatures>()

export const nomenclaturesColumnsTable = [
	columnHelper.accessor('name', {
		header: () => <span>Название</span>,
		cell: (info) => info.getValue(),
	}),
	columnHelper.accessor('timezone', {
		header: () => <span>Часовой пояск</span>,
		cell: (info) => info.getValue(),
	}),
	columnHelper.accessor('version', {
		header: () => <span>Версия</span>,
		cell: (info) => info.getValue(),
	}),
	columnHelper.accessor('last_answer', {
		header: () => <span>Последний ответ</span>,
		cell: (info) => info.getValue(),
	}),
	columnHelper.accessor('status', {
		header: () => <span>Статус</span>,
		cell: (info) => {
			const statusValue = info.getValue()
			console.log('status', statusValue)
			const convStat = convertStatus(statusValue)
			const statusColor = getStatusColor(statusValue === null ? null : Number(statusValue))
			return (
				<div
					style={{
						backgroundColor: statusColor,
						padding: '5px',
						borderRadius: '8px',
					}}
				>
					{convStat}
				</div>
			)
		},
	}),
]
