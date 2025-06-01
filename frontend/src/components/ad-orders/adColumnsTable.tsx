import { createColumnHelper } from '@tanstack/react-table'
import { IAdData, ORDER_TYPE_AD_CONFIG, STATUS_CONFIG } from '@/types/orderTypes'
import dayjs from 'dayjs'

const columnHelper = createColumnHelper<IAdData>()

export const adColumnsTable = [
	columnHelper.accessor('name', {
		header: () => <span>Название</span>,
		cell: (info) => info.getValue(),
		// footer: (info) => info.column.id,
		enableSorting: true,
	}),
	columnHelper.accessor((row) => row.client.name, {
		id: 'client',
		cell: (info) => <i>{info.getValue()}</i>,
		header: () => <span>Номенклатура</span>,
		// footer: (info) => info.column.id,
		enableSorting: true,
	}),
	columnHelper.accessor('broadcast_interval', {
		header: 'Интервал работы заказа',
		cell: (info) => {
			const { lower, upper } = info.getValue() as {
				lower: string
				upper: string
			}
			const formatDate = (dateString: string) => {
				return dayjs(dateString).format('DD/MM/YYYY-HH:mm')
			}
			return `${formatDate(lower)} - ${formatDate(upper)}`
		},
		sortingFn: (rowA, rowB) => {
			const intervalA = rowA.getValue('broadcast_interval') as {
				lower: string
			}
			const intervalB = rowB.getValue('broadcast_interval') as {
				lower: string
			}

			const dateA = dayjs(intervalA.lower)
			const dateB = dayjs(intervalB.lower)

			return dateA.isBefore(dateB) ? -1 : dateA.isAfter(dateB) ? 1 : 0
		},
		enableSorting: true,
	}),
	columnHelper.accessor('broadcast_type', {
		header: 'Тип вещания',
		cell: (info) => {
			const orderTypes = ORDER_TYPE_AD_CONFIG[
				info.getValue() as keyof typeof ORDER_TYPE_AD_CONFIG
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