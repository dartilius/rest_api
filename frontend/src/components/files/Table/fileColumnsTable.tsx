import { IFiles } from '@/types/fileTypes'
import { convertSizeFile } from '@/utils'
import { createColumnHelper } from '@tanstack/react-table'

const columnHelper = createColumnHelper<IFiles>()

export const fileColumnsTable = [
	columnHelper.accessor('name', {
		header: () => <span>Название</span>,
		cell: (info) => info.getValue(),
		enableSorting: true,
	}),
	columnHelper.accessor('size', {
		header: () => <span>Размер</span>,
		cell: (info) => convertSizeFile(info.getValue() as number),
		enableSorting: true,
	}),
	columnHelper.accessor('length', {
		header: () => <span>Длительность</span>,
		cell: (info) => info.getValue(),
		enableSorting: true,
	}),
	columnHelper.accessor('type', {
		header: () => <span>Тип</span>,
		cell: (info) => info.getValue(),
		enableSorting: true,
	}),
	columnHelper.accessor('tags', {
		header: () => <span>Теги</span>,
		cell: (info) => (info.getValue() ? info.getValue().join(', ') : 'Нет тегов'),
		enableSorting: true,
	}),
]
