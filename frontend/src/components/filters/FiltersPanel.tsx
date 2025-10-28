'use client'
import { Search } from '@/components/nomenclatures'
import { useStore } from '@/providers/mobx-provider/MobxProvider'
import { Box, IconButton, Drawer, Typography, Button } from '@mui/material'
import { FC, useState } from 'react'
import { BrcTypeFilter } from './BrcTypeFilter'
import DateRangePickerSinceOrder from './DateRangePickerSinceOrder'
import DateRangePickerUntilOrder from './DateRangePickerUntilOrder'
import DateRangesPickerFilter from './DateRangesPickerFilter'
import { OrderTypeFilter } from './OrderTypeFilter'
import { StatusOrderFilters } from './StatusOrderFilter'
import FilterListIcon from '@mui/icons-material/FilterList'
import CloseIcon from '@mui/icons-material/Close'
import { useMediaQuery, Theme } from '@mui/material'

const FiltersPanel: FC = () => {
	const { ordersStore } = useStore()
	const activeTab = ordersStore.activeTab
	const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down('md'))
	const [isFiltersOpen, setIsFiltersOpen] = useState(false)

	const toggleFilters = () => setIsFiltersOpen(!isFiltersOpen)

	// Мобильный вид - кнопка фильтров и выдвижная панель
	if (isMobile) {
		return (
			<Box
				display='flex'
				justifyContent='center'
				width='100%'
			>
				<IconButton
					onClick={toggleFilters}
					color='primary'
					sx={{ p: 0 }}
				>
					<FilterListIcon fontSize='large' />
					{/* <Typography variant="caption">
            Фильтры
          </Typography> */}
				</IconButton>

				<Drawer
					anchor='right'
					open={isFiltersOpen}
					onClose={toggleFilters}
					sx={{
						'& .MuiDrawer-paper': {
							width: '85vw',
							maxWidth: 400,
							p: 2,
							boxSizing: 'border-box',
						},
					}}
				>
					<Box
						display='flex'
						justifyContent='space-between'
						alignItems='center'
					>
						<Typography variant='h6'>Фильтры</Typography>
						<IconButton onClick={toggleFilters}>
							<CloseIcon />
						</IconButton>
					</Box>

					<Box
						display='flex'
						flexDirection='column'
						gap={1}
					>
						<DateRangesPickerFilter />
						<DateRangePickerSinceOrder />
						<DateRangePickerUntilOrder />

						<Box
							display='flex'
							flexDirection='column'
							gap={2}
						>
							<Search
								nameQueryParams='name'
								label='Название'
							/>
							<Search
								nameQueryParams='client'
								label='Номенклатура'
							/>
						</Box>

						<StatusOrderFilters />

						{activeTab === 0 ? <OrderTypeFilter /> : <BrcTypeFilter />}

						<Button
							variant='contained'
							color='primary'
							onClick={toggleFilters}
							sx={{ mt: 2 }}
						>
							Применить
						</Button>
					</Box>
				</Drawer>
			</Box>
		)
	}

	// Десктопный вид (оригинальный)
	return (
		<Box
			display={'flex'}
			height={'100%'}
			width={'100%'}
			justifyContent={'center'}
			alignItems={'start'}
			gap={2}
		>
			<Box
				display={'flex'}
				flexDirection={'column'}
				justifyContent={'center'}
				alignItems={'center'}
				height={'100%'}
				gap={1}
				width={'100%'}
			>
				<DateRangesPickerFilter />
				<DateRangePickerSinceOrder />
				<DateRangePickerUntilOrder />
			</Box>

			<Box
				display='grid'
				gridTemplateColumns='repeat(2, 1fr)'
				gap={1}
				width={'100%'}
			>
				<Box gridColumn='span 1'>
					<Search
						nameQueryParams='name'
						label='Название'
					/>
				</Box>
				<Box gridColumn='span 1'>
					<Search
						nameQueryParams='client'
						label='Номенклатура'
					/>
				</Box>
				<Box gridColumn='span 1'>
					<StatusOrderFilters />
				</Box>
				<Box gridColumn='span 1'>{activeTab === 0 ? <OrderTypeFilter /> : <BrcTypeFilter />}</Box>
			</Box>
		</Box>
	)
}

export default FiltersPanel
