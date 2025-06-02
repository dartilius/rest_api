'use client'

import { IAdData, ORDER_TYPE_AD_CONFIG, STATUS_CONFIG } from '@/types/orderTypes'
import { Box, Card, CardContent, Typography } from '@mui/material'
import dayjs from 'dayjs'

interface MobileAdViewProps {
	data: IAdData[]
	onRowClick: (id: string) => void
}

const MobileAdViewTable = ({ data, onRowClick }: MobileAdViewProps) => {
	const formatDate = (dateString: string) => {
		return dayjs(dateString).format('DD/MM/YYYY HH:mm')
	}

	return (
		<Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, p: 1 }}>
			{data.map((row) => {
				const status = STATUS_CONFIG[row.status as keyof typeof STATUS_CONFIG] || {
					label: 'Неизвестный статус',
					backgroundColor: 'white',
				}

				const broadcastType =
					ORDER_TYPE_AD_CONFIG[row.broadcast_type as keyof typeof ORDER_TYPE_AD_CONFIG] ||
					'Неизвестный тип'

				return (
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
						onClick={() => onRowClick(row.id)}
					>
						<CardContent>
							<Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
								<Typography
									variant='subtitle1'
									fontWeight='bold'
									sx={{ flexGrow: 1 }}
								>
									{row.name}
								</Typography>
							</Box>
							<Box
                            width={1/2} display={'flex'} alignItems={'center'} justifyContent={'space-around'}
								sx={{
									backgroundColor: status.backgroundColor,
                                    color: status.textColor,
									padding: '4px 8px',
									borderRadius: '8px',
									gap: 0.5,
								}}
							>
								{status.icon && <status.icon fontSize='small' />}
								<Typography
									variant='body2'
									fontWeight='medium'
								>
									{status.label}
								</Typography>
							</Box>
							<Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
								<Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
									<Typography
										variant='caption'
										color='text.secondary'
										sx={{ minWidth: 80 }}
									>
										Клиент:
									</Typography>
									<Typography variant='body2'>{row.client.name}</Typography>
								</Box>

								<Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
									<Typography
										variant='caption'
										color='text.secondary'
										sx={{ minWidth: 80 }}
									>
										Интервал:
									</Typography>
									<Typography variant='body2'>
										{formatDate(row.broadcast_interval.lower)} —{' '}
										{formatDate(row.broadcast_interval.upper)}
									</Typography>
								</Box>

								<Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
									<Typography
										variant='caption'
										color='text.secondary'
										sx={{ minWidth: 80 }}
									>
										Тип вещания:
									</Typography>
									<Box
										sx={{
											display: 'flex',
											alignItems: 'center',
											gap: 0.5,
                                            backgroundColor: broadcastType.backgroundColor,
                                            color: broadcastType.textColor,
                                            borderRadius: 2
										}}
									>
										{broadcastType.icon && (
											<broadcastType.icon
												fontSize='small'
												style={{color: broadcastType.textColor}}
											/>
										)}
										<Typography
											variant='body2'
											fontWeight='medium'
										>
											{broadcastType.label}
										</Typography>
									</Box>
								</Box>
							</Box>
						</CardContent>
					</Card>
				)
			})}
		</Box>
	)
}

export default MobileAdViewTable
