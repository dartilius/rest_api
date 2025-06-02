import { convertStatus } from '@/types/checkStatus'
import { INomenclatures } from '@/types/nomeclaturesType'
import { getStatusColor } from '@/utils'
import { Box, Card, CardContent, Stack, Typography, Chip } from '@mui/material'
import { useRouter } from 'next/navigation'
import { NomenclatureActions } from './NomenclatureActions'

const MobileView = ({ data }: { data: INomenclatures[] }) => {
	const router = useRouter()

	return (
		<>
			{data?.map((row) => (
				<Card
					key={row.id}
				sx={{
							mb: 1,
							boxShadow: 5,
							borderRadius: 2,
							backgroundColor: '#f9fafb',
							transition: 'all 0.3s ease',
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
							<Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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
		</>
	)
}
export default MobileView
