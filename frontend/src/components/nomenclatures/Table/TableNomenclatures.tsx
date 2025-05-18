'use client'
import { FiltersWrapper, NomenclatureActions } from '@/components/nomenclatures'
import CustomPagination from '@/components/Ui/Pagination/CustomPagination'
import { convertStatus } from '@/types/checkStatus'
import { INomenclatures } from '@/types/nomeclaturesType'
import { getStatusColor } from '@/utils'
import {
	Box,
	Card,
	CardContent,
	Chip,
	Stack,
	Table,
	TableBody,
	TableCell,
	TableContainer,
	TableHead,
	TableRow,
	Theme,
	Typography,
	useMediaQuery,
} from '@mui/material'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useRef } from 'react'
import MobileView from './MobileView'
import DesktopView from './DesctopView'

const columns = [
	{ id: 'name', label: 'Название', mobile: true },
	{ id: 'timezone', label: 'Часовой пояс', mobile: false },
	{ id: 'version', label: 'Версия', mobile: false },
	{ id: 'last_answer', label: 'Последний ответ', mobile: true },
	{ id: 'status', label: 'Статус', mobile: true },
	{ id: 'actions', label: 'Действия', mobile: true },
]

type Props = {
	data: INomenclatures[]
	count: any
	limit: number
	page: number
}

export function TableNomenclatures(props: Props) {
	const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down('md'))
	const router = useRouter()
	const topRef = useRef<HTMLDivElement>(null)

	const { data, count } = props

	return (
		<Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
			{isMobile ? (
				<MobileView
					data={data}
					topRef={topRef}
				/>
			) : (
				<DesktopView
					data={data}
					topRef={topRef}
				/>
			)}

			<CustomPagination
				totalItems={count}
				topRef={topRef}
				isMobile={isMobile}
			/>
		</Box>
	)
}
// 	if (isMobile) {
// 		return (
// 			<Box
// 				sx={{
// 					flex: 1,
// 					display: 'flex',
// 					flexDirection: 'column',
// 					overflow: 'hidden',
// 				}}
// 			>
// 				<Box
// 					sx={{
// 						flex: 1,
// 						overflow: 'auto',
// 						p: 1,
// 					}}
// 				>
// 					<div ref={topRef} />
// 					<FiltersWrapper />
// 					{data?.map((row) => (
// 						<Card
// 							key={row.id}
// 							sx={{ mb: 2, boxShadow: 3 }}
// 							onClick={(e) => {
// 								// Обработчик для всей карточки
// 								e.preventDefault()
// 								router.push(`/nomenclatures/${row.id}`)
// 							}}
// 						>
// 							<CardContent>
// 								<Stack spacing={1.5}>
// 									<Typography
// 										variant='subtitle1'
// 										fontWeight='bold'
// 									>
// 										{row.name}
// 									</Typography>
// 									<Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
// 										<Typography
// 											variant='body2'
// 											color='text.secondary'
// 										>
// 											Версия:
// 										</Typography>
// 										<Typography variant='body2'>{row.version}</Typography>
// 									</Box>

// 									<Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
// 										<Typography
// 											variant='body2'
// 											color='text.secondary'
// 										>
// 											Последний ответ:
// 										</Typography>
// 										<Typography variant='body2'>{row.last_answer}</Typography>
// 									</Box>

// 									<Box
// 										sx={{
// 											display: 'flex',
// 											justifyContent: 'space-between',
// 											alignItems: 'center',
// 										}}
// 									>
// 										<Chip
// 											label={convertStatus(row.status)}
// 											sx={{
// 												backgroundColor: getStatusColor(row.status),
// 												color: 'white',
// 												fontSize: '0.75rem',
// 											}}
// 										/>
// 										<NomenclatureActions
// 											id={row.id}
// 											isMobile={isMobile}
// 											onClick={(e: React.MouseEvent) => e.stopPropagation()}
// 										/>
// 									</Box>
// 								</Stack>
// 							</CardContent>
// 						</Card>
// 					))}
// 					{/* <CustomPagination
// 						totalItems={count}
// 						topRef={topRef}
// 					/> */}
// 				</Box>
// 			</Box>
// 		)
// 	}

// 	return (
// 		<Box
// 			sx={{
// 				flex: 1,
// 				display: 'flex',
// 				flexDirection: 'column',
// 				overflow: 'hidden',
// 			}}
// 		>
// 			<TableContainer
// 				sx={{
// 					flex: 1,
// 					overflow: 'auto',
// 					borderRadius: '8px',
// 					bgcolor: 'background.paper',
// 				}}
// 			>
// 				<div ref={topRef} />
// 				<FiltersWrapper />
// 				<Table
// 					stickyHeader
// 					aria-label='sticky table'
// 					className='rounded'
// 				>
// 					<TableHead>
// 						<TableRow>
// 							{columns.map((column) => (
// 								<TableCell
// 									key={column.id}
// 									sx={{
// 										minWidth: 120,
// 										whiteSpace: 'nowrap',
// 										textAlign: 'center',
// 										fontWeight: 'bold',
// 									}}
// 								>
// 									{column.label}
// 								</TableCell>
// 							))}
// 						</TableRow>
// 					</TableHead>
// 					<TableBody>
// 						{data?.map((row: any) => (
// 							<TableRow
// 								hover
// 								role='checkbox'
// 								tabIndex={-1}
// 								key={row?.id}
// 							>
// 								{columns?.map((column) => {
// 									const value = row[column.id]
// 									return (
// 										<TableCell
// 											key={column.id}
// 											sx={{
// 												whiteSpace: 'nowrap',
// 												overflow: 'hidden',
// 												textOverflow: 'ellipsis',
// 												textAlign: 'center',
// 												maxWidth: 200,
// 											}}
// 										>
// 											{column.id === 'status' ? (
// 												<Box
// 													sx={{
// 														display: 'inline-block',
// 														padding: '4px 8px',
// 														borderRadius: '8px',
// 														backgroundColor: getStatusColor(value),
// 														color: 'white',
// 													}}
// 												>
// 													{convertStatus(value)}
// 												</Box>
// 											) : column.id === 'actions' ? (
// 												<NomenclatureActions id={row.id} />
// 											) : (
// 												<Link href={`/nomenclatures/${row.id}`}>{value}</Link>
// 											)}
// 										</TableCell>
// 									)
// 								})}
// 							</TableRow>
// 						))}
// 					</TableBody>
// 				</Table>
// 				<CustomPagination
// 					totalItems={count}
// 					topRef={topRef}
// 					isMobile={isMobile}
// 				/>
// 			</TableContainer>
// 		</Box>
// 	)
// }
