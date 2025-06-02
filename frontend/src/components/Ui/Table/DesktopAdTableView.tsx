'use client'
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table'
import { IAdData } from '@/types/orderTypes'
import { adColumnsTable } from '@/components/ad-orders/adColumnsTable'


interface DesktopAdViewProps {
  data: IAdData[]
  onRowClick: (id: string) => void
}

const DesktopAdTableView = ({ data, onRowClick }: DesktopAdViewProps) => {
  const table = useReactTable({
    data,
    columns: adColumnsTable,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    enableSorting: true,
  })

  return (
    <table className='w-full'>
      <thead>
        {table.getHeaderGroups().map((headerGroup) => (
          <tr
            key={headerGroup.id}
            className='h-16 border-2 border-slate-300'
          >
            {headerGroup.headers.map((header) => (
              <th
                key={header.id}
                style={{
                  width: header.id === 'status' ? '160px' : 'auto',
                }}
              >
                {header.isPlaceholder ? null : (
                  <div
                    className='cursor-pointer'
                    {...{
                      onClick: header.column.getToggleSortingHandler(),
                    }}
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
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
            onClick={() => onRowClick(row.original.id)}
          >
            {row.getVisibleCells().map((cell) => (
              <td
                key={cell.id}
                className='text-center cursor-pointer p-2'
              >
                {flexRender(cell.column.columnDef.cell, cell.getContext())}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default DesktopAdTableView