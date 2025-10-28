'use client'
import { INomenclatures } from '@/types/nomeclaturesType'
import { Box, Theme, useMediaQuery } from '@mui/material'
import { useRef } from 'react'
import DesktopNomenclaturesVeiw from './desktop/DesktopVeiw'
import MobileView from './MobileView'

type Props = {
	data: INomenclatures[]
	count: any
	limit: number
	page: number
}

export function TableNomenclatures(props: Props) {
	const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down('md'))
	const topRef = useRef<HTMLDivElement>(null)
	const { data, count } = props

	return (
		<Box
			sx={{
				width: '100%',
				height: '100%',
				display: 'flex',
				flexDirection: 'column',
				overflow: 'hidden',
			}}
		>
			<Box
				sx={{
					flex: 1,
					display: 'flex',
					flexDirection: 'column',
					overflow: 'hidden',
				}}
			>
				<Box
					ref={topRef}
					sx={{ height: '1px', width: '100%' }} // Невидимый элемент для скролла
				/>

				<Box
					sx={{
						flex: 1,
						overflow: 'auto',
						WebkitOverflowScrolling: 'touch', // Для плавного скролла в iOS
						overscrollBehavior: 'contain', // Предотвращает отскок страницы
						p: 1,
					}}
				>
					{isMobile ? (
						<MobileView data={data} />
					) : (
						<DesktopNomenclaturesVeiw
							data={data}
							countNomenclatures={count}
						/>
					)}
				</Box>
			</Box>
		</Box>
	)
}
