'use client'

import { INomenclaturesListResponse } from '@/types/nomeclaturesType'
import { Box, Theme, useMediaQuery } from '@mui/material'
import { useRef } from 'react'
import MobileView from '../Table/MobileView'
import { DesktopView } from './DesktopView/DesktopView'

interface Props {
	data: INomenclaturesListResponse['results']
	count: number
}

export function PageWrapper(props: Props) {
	const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down('md'))
	const topRef = useRef<HTMLDivElement>(null)

	const { data, count } = props

	return (
		<Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
			{isMobile ? (
				<MobileView
					data={data}
					topRef={topRef}
					count={count}
				/>
			) : (
				<DesktopView
					data={data}
					topRef={topRef}
					count={count}
				/>
			)}
		</Box>
	)
}
