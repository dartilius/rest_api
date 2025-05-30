import CustomPagination from '@/components/Ui/Pagination/CustomPagination'
import { convertStatus } from '@/types/checkStatus'
import { INomenclatures } from '@/types/nomeclaturesType'
import { getStatusColor } from '@/utils'
import { Box, Card, CardContent, Chip, Stack, Typography } from '@mui/material'
import { useRouter } from 'next/navigation'
import { FiltersWrapper } from '../FiltersWrapper'
import { NomenclatureActions } from './NomenclatureActions'

const MobileView = ({
	data,
	topRef,
	count,
}: {
	data: INomenclatures[]
	topRef: React.RefObject<HTMLDivElement>
	count: number
}) => {
	const router = useRouter()

	return (
		<Box
			sx={{
				flex: 1,
				display: 'flex',
				flexDirection: 'column',
				minHeight: 0, // Ключевое свойство для iOS
				WebkitOverflowScrolling: 'touch',
			}}
		>
			<FiltersWrapper />
			<Box
				sx={{
					flex: 1,
					overflow: 'auto',
					WebkitOverflowScrolling: 'touch',
					position: 'relative',
					p: 1,
					overscrollBehavior: 'contain',
				}}
			>
				<div ref={topRef} />
				{data?.map((row) => (
					<Card
						key={row.id}
						sx={{
							mb: 2,
							transform: 'translateZ(0)',
							willChange: 'transform',
							boxShadow: 5,
							background: '#d1d5db',
							'&:active': {
								transform: 'scale(0.98)',
							},
						}}
						onClick={(e) => {
							e.preventDefault()
							router.push(`/nomenclatures/${row.id}`)
						}}
					>
						<CardContent>
							<Stack spacing={1.5}>
								<Typography
									variant='subtitle1'
									fontWeight='bold'
								>
									{row.name}
								</Typography>
								<Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
									<Typography
										variant='body2'
										color='text.secondary'
									>
										Версия:
									</Typography>
									<Typography variant='body2'>{row.version}</Typography>
								</Box>
								<Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
									<Typography
										variant='body2'
										color='text.secondary'
									>
										Последний ответ:
									</Typography>
									<Typography variant='body2'>{row.last_answer}</Typography>
								</Box>
								<Box
									sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
								>
									<Chip
										label={convertStatus(row.status)}
										sx={{
											backgroundColor: getStatusColor(row.status),
											color: 'white',
											fontSize: '0.75rem',
										}}
									/>
									<NomenclatureActions
										id={row.id}
										isMobile={true}
										onClick={(e: React.MouseEvent) => e.stopPropagation()}
									/>
								</Box>
							</Stack>
						</CardContent>
					</Card>
				))}
			</Box>

			<CustomPagination
				totalItems={count}
				topRef={topRef}
				isMobile={true}
			/>
		</Box>
	)
}
export default MobileView
