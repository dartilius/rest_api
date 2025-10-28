import { Stack, Typography } from '@mui/material'

import { Card, CardContent } from '@mui/material'

import { Box } from '@mui/material'

import FiltersWrapper from '@/app/files/components/FilterWrapper/FiltersWrapper'
import { IFilesListResponse } from '@/types/fileTypes'
import { convertSizeFile } from '@/utils'
import { useRouter } from 'next/navigation'

const MobileView = ({
	data,
	topRef,
}: {
	data: IFilesListResponse['results']
	topRef: React.RefObject<HTMLDivElement>
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
				background: 'var(--foreground)',
			}}
		>
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
				<FiltersWrapper />
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
							router.push(`/files/${row.id}`)
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
										Название:
									</Typography>
									<Typography variant='body2'>{row.name}</Typography>
								</Box>
								<Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
									<Typography
										variant='body2'
										color='text.secondary'
									>
										Размер:
									</Typography>
									<Typography variant='body2'>{convertSizeFile(row.size)}</Typography>
								</Box>
								<Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
									<Typography
										variant='body2'
										color='text.secondary'
									>
										Длительность:
									</Typography>
									<Typography variant='body2'>{row.length}</Typography>
								</Box>
								<Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
									<Typography
										variant='body2'
										color='text.secondary'
									>
										Тип:
									</Typography>
									<Typography variant='body2'>{row.type}</Typography>
								</Box>
								<Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
									<Typography
										variant='body2'
										color='text.secondary'
									>
										Теги:
									</Typography>
									<Typography variant='body2'>
										{row.tags ? row.tags.join(', ') : 'Нет тегов'}
									</Typography>
								</Box>
							</Stack>
						</CardContent>
					</Card>
				))}
			</Box>
		</Box>
	)
}
export default MobileView
