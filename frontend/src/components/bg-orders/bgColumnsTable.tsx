import { createColumnHelper } from '@tanstack/react-table'
import { IBgData } from '@/types/orderTypes'
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
      const formatDate = (dateString: string) =>
        dayjs(dateString).format('DD/MM/YYYY-HH:mm')
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
      const orderTypes = {
        0: 'Музыка',
        1: 'Видео',
        2: 'Картинки',
        3: 'Бегущая строка',
      }
      return (
        orderTypes[info.getValue() as keyof typeof orderTypes] ||
        'Неизвестный тип'
      )
    },
    enableSorting: true,
  }),
  columnHelper.accessor('status', {
    header: 'Статус',
    cell: (info) => {
      const statusMapping = {
        0: {
          label: 'Ожидает эфира',
          backgroundColor: 'rgba(255, 167, 86, 0.4)',
        },
        1: { label: 'В эфире', backgroundColor: 'rgba(0, 182, 155, 0.4)' },
        2: { label: 'Завершен', backgroundColor: 'rgba(128, 128, 128, 0.4)' },
        3: { label: 'Отменен', backgroundColor: 'rgba(239, 56, 40, 0.4)' },
        4: { label: 'Ошибка', backgroundColor: 'rgba(239, 56, 40, 0.4)' },
      }
      const status = statusMapping[
        info.getValue() as keyof typeof statusMapping
      ] || { label: 'Неизвестный статус', backgroundColor: 'white' }

      return (
        <div
          style={{
            backgroundColor: status.backgroundColor,
            padding: '5px',
            borderRadius: '8px',
          }}
        >
          {status.label}
        </div>
      )
    },
    enableSorting: true,
  }),
]
