import { convertStatus } from '@/types/checkStatus'
import { INomenclatures } from '@/types/nomeclaturesType'
import { getStatusColor } from '@/utils'
import {
	Box,
	TableContainer,
	Table,
	TableHead,
	TableRow,
	TableCell,
	TableBody,
} from '@mui/material'
import Link from 'next/link'
import { FiltersWrapper } from '../FiltersWrapper'
import { NomenclatureActions } from './NomenclatureActions'

const columns = [
	{ id: 'name', label: 'Название', mobile: true },
	{ id: 'timezone', label: 'Часовой пояс', mobile: false },
	{ id: 'version', label: 'Версия', mobile: false },
	{ id: 'last_answer', label: 'Последний ответ', mobile: true },
	{ id: 'status', label: 'Статус', mobile: true },
	{ id: 'actions', label: 'Действия', mobile: true },
]

const DesktopView = ({
	data,
	topRef,
}: {
	data: INomenclatures[]
	topRef: React.RefObject<HTMLDivElement>
}) => (
	<Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
		<TableContainer
			sx={{ flex: 1, overflow: 'auto', borderRadius: '8px', bgcolor: 'background.paper' }}
		>
			<div ref={topRef} />
			<FiltersWrapper />
			<Table
				stickyHeader
				aria-label='sticky table'
				className='rounded'
			>
				<TableHead>
					<TableRow>
						{columns.map((column) => (
							<TableCell
								key={column.id}
								sx={{
									minWidth: 120,
									whiteSpace: 'nowrap',
									textAlign: 'center',
									fontWeight: 'bold',
								}}
							>
								{column.label}
							</TableCell>
						))}
					</TableRow>
				</TableHead>
				<TableBody>
					{data?.map((row) => (
						<TableRow
							hover
							role='checkbox'
							tabIndex={-1}
							key={row.id}
						>
							{columns.map((column) => {
								const value = row[column.id as keyof INomenclatures]
								return (
									<TableCell
										key={column.id}
										sx={{
											whiteSpace: 'nowrap',
											overflow: 'hidden',
											textOverflow: 'ellipsis',
											textAlign: 'center',
											maxWidth: 200,
										}}
									>
										{column.id === 'status' ? (
											<Box
												sx={{
													display: 'inline-block',
													padding: '4px 8px',
													borderRadius: '8px',
													backgroundColor: getStatusColor(Number(value)),
													color: 'white',
												}}
											>
												{convertStatus(Number(value))}
											</Box>
										) : column.id === 'actions' ? (
											<NomenclatureActions id={row.id} />
										) : (
											<Link href={`/nomenclatures/${row.id}`}>{value}</Link>
										)}
									</TableCell>
								)
							})}
						</TableRow>
					))}
				</TableBody>
			</Table>
		</TableContainer>
	</Box>
)
export default DesktopView
