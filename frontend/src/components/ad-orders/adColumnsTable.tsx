import { createColumnHelper } from '@tanstack/react-table'
import { IAdData } from '@/types/orderTypes'
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
      const orderTypes = {
        0: 'По времени работы точки',
        1: 'Начало работы + смещение по времени',
        2: 'Конец работы – смещение по времени',
        3: 'С открытия до конкретного часа',
        4: 'С фиксированного часа до закрытия',
        5: 'Старт по событию',
      } as const
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
