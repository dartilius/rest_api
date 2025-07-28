import { convertStatus } from '@/types/checkStatus'
import { INomenclatures } from '@/types/nomeclaturesType'
import { getStatusColor } from '@/utils'
import { createColumnHelper } from '@tanstack/react-table'
import { NomenclatureActions } from '../NomenclatureActions'

const columnHelper = createColumnHelper<INomenclatures>()

export const nomenclaturesColumnsTable = [
	columnHelper.accessor('name', {
		header: () => <span>Название</span>,
		cell: (info) => info.getValue(),
		enableSorting: true,
	}),
	columnHelper.accessor('timezone', {
		header: () => <span>Часовой пояс</span>,
		cell: (info) => info.getValue(),
		enableSorting: true,
	}),
	columnHelper.accessor('version', {
		header: () => <span>Версия</span>,
		cell: (info) => info.getValue(),
		enableSorting: true,
	}),
	columnHelper.accessor('last_answer', {
		header: () => <span>Последний ответ</span>,
		cell: (info) => info.getValue(),
		enableSorting: true,
	}),
	columnHelper.accessor('status', {
		header: () => <span>Статус</span>,
		cell: (info) => (
			<span
				style={{
					display: 'inline-block',
					padding: '4px 8px',
					borderRadius: '8px',
					backgroundColor: getStatusColor(info.getValue()),
					color: 'white',
					textWrap: 'nowrap',
				}}
			>
				{convertStatus(info.getValue())}
			</span>
		),
		enableSorting: true,
	}),
	columnHelper.accessor('actions', {
		header: () => <span>Действия</span>,
		cell: (info) => <NomenclatureActions id={info.row.original.id} />,
		enableSorting: true,
	}),
]
