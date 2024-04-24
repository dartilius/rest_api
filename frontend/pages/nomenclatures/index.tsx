// pages/nomenclatures/index.tsx
import { GetServerSideProps, InferGetServerSidePropsType } from 'next'
import styles from './Nomenclatures.module.scss'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import {
    ColumnDef,
    ColumnFiltersState,
    SortingState,
    VisibilityState,
    flexRender,
    getCoreRowModel,
    getFilteredRowModel,
    getPaginationRowModel,
    getSortedRowModel,
    useReactTable,
  } from "@tanstack/react-table"
  import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
  } from "@/components/ui/table"

export type Nomenclatures = {
    created: string
    description: string
    id: string
    is_active: boolean
    name: string
    owner: {
        email: string
        first_name: string
        id: string
        last_name: string
        middle_name: string
        phone: string
        role: null
        username: string
    }
    status: number
    timezone: string
    version: string
}

interface NomenclaturesProps {
  data: Nomenclatures[]
}

export const getServerSideProps: GetServerSideProps<NomenclaturesProps> = async () => {
    const res = await fetch('http://192.168.0.180:8000/api/nomenclatures/')
    console.log(res);
    
    const data = await res.json();
  
    // const data = json.data || []; // Provide a fallback as an empty array
  
    return {
      props: {
        data: data || [],
      },
    }
}

export const columns: ColumnDef<Nomenclatures>[] = [
    {
        accessorKey: 'name',
        header: 'Название',
        cell: ({ row }) => {
            <div className='capilitate'>{row.getValue('name')}</div>
        }
    },
    {
        accessorKey: 'description',
        header: 'Описание',
        cell: ({ row }) => {
            <div className='capilitate'>{row.getValue('description')}</div>
        }
    },
    {
        accessorKey: 'id',
        header: 'id',
        cell: ({ row }) => {
            <div className='capilitate'>{row.getValue('id')}</div>
        }
    },
    {
        accessorKey: 'is_active',
        header: 'Активность',
        cell: ({ row }) => {
            <div className='capilitate'>{row.getValue('is_active')}</div>
        }
    },
    {
        accessorKey: 'id',
        header: 'id',
        cell: ({ row }) => {
            <div className='capilitate'>{row.getValue('id')}</div>
        }
    },
    {
        accessorKey: 'status',
        header: 'status',
        cell: ({ row }) => {
            <div className='capilitate'>{row.getValue('status')}</div>
        }
    }
    
]

export default function Nomenclatures({ data }: InferGetServerSidePropsType<typeof getServerSideProps>) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  })
  

  if (!data) {
    return <div>Loading...</div>
  }

  console.log(data);


  

  return (
    <>
      <div className={styles.breadcrumb}>
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href="/">Главная</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbLink href="/nomenclatures">
                <BreadcrumbPage>
                  Номенклатуры
                </BreadcrumbPage>
              </BreadcrumbLink>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </div>
      {/* <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  )
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div> */}
      {/* <div className={styles.container}>
        {data.map((user: any) => (
          <div key={user.id}>
            <p>Название: {user.name}</p>
            <p>Описание: {user.price}</p>
            <p>id: {user.id}</p>
          </div>
        ))}
      </div> */}
    </>
  )
}
