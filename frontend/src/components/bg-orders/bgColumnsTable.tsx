import { createColumnHelper } from '@tanstack/react-table'
import { IBgData, ORDER_TYPE_BG_CONFIG, STATUS_CONFIG } from '@/types/orderTypes'
import dayjs from 'dayjs'

const columnHelper = createColumnHelper<IBgData>()

export const bgColumnsTable = [
	columnHelper.accessor('name', {
		header: () => <span>Название</span>,
		cell: (info) => info.getValue(),
		enableSorting: true,
	}),
	columnHelper.accessor((row) => row.client.name, {
		id: 'client',
		cell: (info) => <i>{info.getValue()}</i>,
		header: () => <span>Номенклатура</span>,
		enableSorting: true,
	}),
	columnHelper.accessor('broadcast_interval', {
		header: 'Интервал работы заказа',
		cell: (info) => {
			const { lower, upper } = info.getValue()
			const formatDate = (dateString: string) => dayjs(dateString).format('DD/MM/YYYY-HH:mm')
			return `${formatDate(lower)} - ${formatDate(upper)}`
		},
		sortingFn: (rowA, rowB) => {
			const dateA = dayjs(rowA.original.broadcast_interval.lower)
			const dateB = dayjs(rowB.original.broadcast_interval.lower)
			return dateA.diff(dateB)
		},
		enableSorting: true,
	}),
	columnHelper.accessor('order_type', {
		header: 'Тип',
		cell: (info) => {
			const orderTypes = ORDER_TYPE_BG_CONFIG[
				info.getValue() as keyof typeof ORDER_TYPE_BG_CONFIG
			] || { label: 'Неизвестный статус', backgroundColor: 'white' }
			return (
				<div
					className='flex items-center gap-1 p-1 rounded-lg'
					style={{
						backgroundColor: orderTypes.backgroundColor,
						color: orderTypes.textColor,
					}}
				>
					{orderTypes.icon && <orderTypes.icon fontSize='small' />}
					<span>{orderTypes.label}</span>
				</div>
			)
		},
		enableSorting: true,
	}),
	columnHelper.accessor('status', {
		header: 'Статус',
		cell: (info) => {
			const status = STATUS_CONFIG[info.getValue() as keyof typeof STATUS_CONFIG] || {
				label: 'Неизвестный статус',
				backgroundColor: 'white',
				icon: null,
			}
			return (
				<div
					className={`flex items-center gap-1 rounded-lg px-2 py-1`}
					style={{ backgroundColor: status.backgroundColor, color: status.textColor }}
				>
					{status.icon && <status.icon fontSize='small' />}
					<span>{status.label}</span>
				</div>
			)
		},
		enableSorting: true,
	}),
]
