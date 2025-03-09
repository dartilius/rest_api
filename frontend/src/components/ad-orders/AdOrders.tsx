'use client'

import { useStore } from '@/providers/mobx-provider/MobxProvider'
import { IAdData } from '@/types/orderTypes'
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
import { useEffect, useState } from 'react'

const AdOrders = () => {
  const { ordersStore } = useStore()
  const [data, setData] = useState<IAdData[]>([])
  const columnHelper = createColumnHelper<IAdData>()

  useEffect(() => {
    if (ordersStore.dataAdResponse?.results)
      setData(toJS(ordersStore.dataAdResponse?.results))
  }, [ordersStore.dataAdResponse?.results])

  const columns = [
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
          4: 'С открытия до конкретного часа',
          5: 'С фиксированного часа до закрытия',
          6: 'Старт по событию',
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
    router.push(`orders/ad/${id}`)
  }
  return (
    <div className='p-2 w-full h-full'>
      <table className='w-full '>
        <thead className='sticky'>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id} className='h-16 border-2 border-slate-300'>
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
                <td key={cell.id} className='text-center cursor-pointer p-2'>
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
    </div>
  )
}
export default observer(AdOrders)
