'use client'

import { useStore } from '@/providers/mobx-provider/MobxProvider'
import { ordersStore } from '@/store'
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table'
import dayjs from 'dayjs'
import { toJS } from 'mobx'
import { observer } from 'mobx-react'
import { useRouter } from 'next/navigation'
import React from 'react'

interface Client {
  id: string
  name: string
}
interface BroadcastInterval {
  lower: string
  upper: string
}

interface IBgData {
  id: string
  name: string
  client: Client
  order_type: number
  status: number
  broadcast_interval: BroadcastInterval
}
const dataBg: IBgData[] = [
  {
    id: 'c8f35885-0673-42f9-8910-0921b6576dea',
    name: 'картиночки для теста',
    client: {
      id: 'd6578da7-50e0-49f4-81bd-eba08474b950',
      name: '!!! #Test 8 Борисов И.',
    },
    order_type: 2,
    status: 1,
    broadcast_interval: {
      lower: '2025-02-12 09:00:00',
      upper: '2025-02-28 18:00:00',
    },
  },
  {
    id: 'c8f35885-0673-42f9-8910-0921b6576dea',
    name: 'картиночки для теста',
    client: {
      id: 'd6578da7-50e0-49f4-81bd-eba08474b950',
      name: '!!! #Test 8 Борисов И.',
    },
    order_type: 1,
    status: 2,
    broadcast_interval: {
      lower: '2025-02-12 09:00:00',
      upper: '2025-02-28 18:00:00',
    },
  },
  {
    id: 'c8f35885-0673-42f9-8910-0921b6576dea',
    name: 'картиночки для теста',
    client: {
      id: 'd6578da7-50e0-49f4-81bd-eba08474b950',
      name: '!!! #Test 8 Борисов И.',
    },
    order_type: 0,
    status: 0,
    broadcast_interval: {
      lower: '2025-02-12 09:00:00',
      upper: '2025-02-28 18:00:00',
    },
  },
  {
    id: 'c8f35885-0673-42f9-8910-0921b6576dea',
    name: 'картиночки для теста',
    client: {
      id: 'd6578da7-50e0-49f4-81bd-eba08474b950',
      name: '!!! #Test 8 Борисов И.',
    },
    order_type: 3,
    status: 3,
    broadcast_interval: {
      lower: '2025-01-12 09:00:00',
      upper: '2025-02-28 18:00:00',
    },
  },
  {
    id: 'c8f35885-0673-42f9-8910-0921b6576dea',
    name: 'картиночки для теста',
    client: {
      id: 'd6578da7-50e0-49f4-81bd-eba08474b950',
      name: '!!! #Test 8 Борисов И.',
    },
    order_type: 1,
    status: 4,
    broadcast_interval: {
      lower: '2025-03-12 09:00:00',
      upper: '2025-05-28 18:00:00',
    },
  },
  {
    id: 'c8f35885-0673-42f9-8910-0921b6576dea',
    name: 'картиночки для теста',
    client: {
      id: 'd6578da7-50e0-49f4-81bd-eba08474b950',
      name: '!!! #Test 8 Борисов И.',
    },
    order_type: 0,
    status: 1,
    broadcast_interval: {
      lower: '2025-02-01 09:00:00',
      upper: '2025-02-28 18:00:00',
    },
  },
  {
    id: 'c8f35885-0673-42f9-8910-0921b6576dea',
    name: 'картиночки для теста',
    client: {
      id: 'd6578da7-50e0-49f4-81bd-eba08474b950',
      name: '!!! #Test 8 Борисов И.',
    },
    order_type: 2,
    status: 3,
    broadcast_interval: {
      lower: '2025-01-11 09:00:00',
      upper: '2025-02-28 18:00:00',
    },
  },
  {
    id: 'c8f35885-0673-42f9-8910-0921b6576dea',
    name: 'картиночки для теста',
    client: {
      id: 'd6578da7-50e0-49f4-81bd-eba08474b950',
      name: '!!! #Test 8 Борисов И.',
    },
    order_type: 3,
    status: 0,
    broadcast_interval: {
      lower: '2025-03-12 09:00:00',
      upper: '2025-04-28 18:00:00',
    },
  },
  {
    id: 'c8f35885-0673-42f9-8910-0921b6576dea',
    name: 'картиночки для теста',
    client: {
      id: 'd6578da7-50e0-49f4-81bd-eba08474b950',
      name: '!!! #Test 8 Борисов И.',
    },
    order_type: 1,
    status: 1,
    broadcast_interval: {
      lower: '2025-01-12 09:00:00',
      upper: '2025-02-28 18:00:00',
    },
  },
  {
    id: 'c8f35885-0673-42f9-8910-0921b6576dea',
    name: 'картиночки для теста',
    client: {
      id: 'd6578da7-50e0-49f4-81bd-eba08474b950',
      name: '!!! #Test 8 Борисов И.',
    },
    order_type: 3,
    status: 2,
    broadcast_interval: {
      lower: '2025-02-11 09:00:00',
      upper: '2025-02-28 18:00:00',
    },
  },
]

const columnHelper = createColumnHelper<IBgData>()

const columns = [
  columnHelper.accessor('name', {
    header: () => <span>Name</span>,
    cell: (info) => info.getValue(),
    // footer: (info) => info.column.id,
    enableSorting: true,
  }),
  columnHelper.accessor((row) => row.client.name, {
    id: 'client',
    cell: (info) => <i>{info.getValue()}</i>,
    header: () => <span>Client Name</span>,
    // footer: (info) => info.column.id,
    enableSorting: true,
  }),
  columnHelper.accessor('broadcast_interval', {
    header: 'Broadcast Interval',
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
      const intervalA = rowA.getValue('broadcast_interval') as { lower: string }
      const intervalB = rowB.getValue('broadcast_interval') as { lower: string }

      const dateA = dayjs(intervalA.lower)
      const dateB = dayjs(intervalB.lower)

      return dateA.isBefore(dateB) ? -1 : dateA.isAfter(dateB) ? 1 : 0
    },
    enableSorting: true,
  }),
  columnHelper.accessor('order_type', {
    header: 'Order Type',
    cell: (info) => {
      const orderTypes = {
        0: 'Музыка',
        1: 'Видео',
        2: 'Картинки',
        3: 'Бегущая строка',
      } as const
      return (
        orderTypes[info.getValue() as keyof typeof orderTypes] ||
        'Неизвестный тип'
      )
    },
    enableSorting: true,
  }),
  columnHelper.accessor('status', {
    header: 'Status',
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

const BgOrders = () => {
  const { ordersStore } = useStore()
  console.log('data', toJS(ordersStore.dataBg))

  const [data] = React.useState<IBgData[]>(() => [...dataBg])
  const router = useRouter()
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    enableSorting: true,
  })
  const handleRowClick = (id: string) => {
    // Переход на страницу с расшифровкой
    router.push(`orders/bg/${id}`)
  }

  return (
    <div className='p-2 w-full'>
      {' '}
      {ordersStore.dataBg.length < 1 ? (
        <p>loading</p>
      ) : (
        <table className='w-full h-full'>
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr
                key={headerGroup.id}
                className='h-16 border-2 border-slate-300'
              >
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    style={{ width: header.id === 'status' ? '160px' : 'auto' }}
                  >
                    {header.isPlaceholder ? null : (
                      <div
                        className='cursor-pointer'
                        {...{
                          onClick: header.column.getToggleSortingHandler(),
                        }}
                      >
                        {flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                        {/* Индикатор сортировки */}
                        <span>
                          {header.column.getIsSorted()
                            ? header.column.getIsSorted() === 'asc'
                              ? ' 🔼'
                              : ' 🔽'
                            : ''}
                        </span>
                      </div>
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className='border-2 border-slate-300 text-center h-16'
                onClick={() => handleRowClick(row.original.id)}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className='text-center cursor-pointer'>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
          <tfoot>
            {table.getFooterGroups().map((footerGroup) => (
              <tr key={footerGroup.id}>
                {footerGroup.headers.map((header) => (
                  <th key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.footer,
                          header.getContext()
                        )}
                  </th>
                ))}
              </tr>
            ))}
          </tfoot>
        </table>
      )}
    </div>
  )
}

export default observer(BgOrders)
