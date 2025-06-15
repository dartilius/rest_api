'use client'
import { useStore } from '@/providers/mobx-provider/MobxProvider'
import { IBgData, IDataBgResponse } from '@/types/orderTypes'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import { observer } from 'mobx-react'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { useEffect, useRef, useState } from 'react'
import FiltersPanel from '../filters/FiltersPanel'
import AppBar from '@mui/material/AppBar'
import { Theme, Typography, useMediaQuery } from '@mui/material'
import CreateBgOrderModal from './CreateBgOrderModal'
import CustomPagination from '../Ui/Pagination/CustomPagination'
import DesktopBgTableView from '../Ui/Table/DesktopBgTableView'
import MobileBgTableView from '../Ui/Table/MobileBgTableView'

interface IProps {
	dataResponse: IDataBgResponse
}
const BgOrders = ({ ...props }: IProps) => {
	const { dataResponse } = props
	const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down('md'))
	const { ordersStore } = useStore()
	const [data, setData] = useState<IBgData[]>([])
	const router = useRouter()
	const pathname = usePathname()
	const searchParams = useSearchParams()
	const topRef = useRef<HTMLDivElement>(null)

	useEffect(() => {
		const params = new URLSearchParams(searchParams)
		if (!params.has('page')) {
			params.set('page', '1')
			router.replace(`${pathname}?${params.toString()}`)
		}

		setData(dataResponse.results)
		ordersStore.setTotalCountBg(dataResponse.count)
		ordersStore.setActiveTabs(0)
	}, [])

	const handleRowClick = (id: string) => {
		// Переход на страницу с расшифровкой
		router.push(`bgorders/${id}`)
	}

	return (
		<Paper
			elevation={4}
			sx={{
				width: '100%',
				height: '100%',
				display: 'flex',
				flexDirection: 'column',
			}}
		>
			<AppBar
				position='sticky'
				sx={{
					// zIndex: (theme) => theme.zIndex.drawer + 1,
					top: 0,
					backgroundColor: 'background.paper',
				}}
			>
				{isMobile ? (
					<Box
						display={'flex'}
						justifyContent={'center'}
						alignItems={'center'}
						width={'100%'}
						height={'100%'}
						padding={1}
						gap={1}
					>
						<FiltersPanel />
						<Box
							sx={{
								display: 'flex',
								justifyContent: 'center',
								alignItems: 'center',
								width: '100%',
								height: '100%',
							}}
						>
							<Typography
								noWrap
								component={'span'}
								sx={{
									fontSize: '1.5rem',
									fontStyle: 'oblique',
									textTransform: 'uppercase',
									color: '#152c4d',
								}}
							>
								Фоновые
							</Typography>
						</Box>
						<CreateBgOrderModal />
					</Box>
				) : (
					<Box
						display={'flex'}
						flexDirection={'column'}
						justifyContent={'center'}
						alignItems={'center'}
						width={'100%'}
						height={'100%'}
						padding={1}
						gap={1}
					>
						<Box
							sx={{
								display: 'flex',
								justifyContent: 'center',
								alignItems: 'center',
								width: '100%', // Занимает всю доступную ширину
								height: '100%',
								gap: 2,
							}}
						>
							<Typography
								noWrap
								component={'span'}
								sx={{
									fontSize: '1.5rem',
									fontStyle: 'oblique',
									textTransform: 'uppercase',
									color: '#152c4d',
								}}
							>
								Фоновые
							</Typography>
							<CreateBgOrderModal />
						</Box>

						<FiltersPanel />
					</Box>
				)}
			</AppBar>
			<div
				className='p-2 w-full overflow-auto'
				ref={topRef}
			>
				{data.length < 1 ? (
					<p>Нет данных</p>
				) : isMobile ? (
					<MobileBgTableView
						data={data}
						onRowClick={handleRowClick}
					/>
				) : (
					<DesktopBgTableView
						data={data}
						onRowClick={handleRowClick}
					/>
				)}
			</div>
			<Box
				sx={{
					flexShrink: 0,
					p: 0,
					display: 'flex',
					justifyContent: 'center',
					backgroundColor: 'background.paper',
				}}
			>
				<CustomPagination
					totalItems={dataResponse.count}
					topRef={topRef}
				/>
			</Box>
		</Paper>
	)
}

export default observer(BgOrders)
