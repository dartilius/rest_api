'use client'
import { FC, useState } from 'react'
import { Box, IconButton, Paper } from '@mui/material'
import FilterListIcon from '@mui/icons-material/FilterList'
import DateRangesPickerFilter from './DateRangesPickerFilter'
import { useStore } from '@/providers/mobx-provider/MobxProvider'
import { Search } from '@/app/nomenclatures/components'
import { BrcTypeFilter } from './BrcTypeFilter'
import { OrderTypeFilter } from './OrderTypeFilter'
import DateRangePickerSinceOrder from './DateRangePickerSinceOrder'
import DateRangePickerUntilOrder from './DateRangePickerUntilOrder'
import { StatusOrderFilters } from './StatusOrderFilter'

const FiltersPanel: FC = () => {
	const { ordersStore } = useStore()
	const activeTab = ordersStore.activeTab
	// const [isFiltersPanelOpen, setIsFiltersPanelOpen] = useState(false)

	// const handleFilterClick = () => {
	// 	setIsFiltersPanelOpen((prev) => !prev)
	// }

	return (
		<Box
			display={'flex'}
			height={'100%'}
			width={'100%'}
			justifyContent={'center'}
			alignItems={'start'}
			gap={2}
		>
			{/* <div className='flex flex-row items-center justify-center gap-4'> */}

			{/* <IconButton onClick={handleFilterClick}>
					<FilterListIcon />
				</IconButton> */}
			{/* </div> */}
			{/* {isFiltersPanelOpen && (
				<Box
					position={'absolute'}
					top={64}
					left={0}
					width={'100%'}
					boxSizing={'border-box'}
					padding={1}
					zIndex={1}
				>
					<Paper
						elevation={6}
						
						className='absolute flex flex-row gap-1 w-full p-2 bg-gray-300 rounded-lg'
					> */}
			<Box
				display={'flex'}
				flexDirection={'column'}
				height={'100%'}
				gap={2}
			>
				<DateRangesPickerFilter />
				{/** настроить параметры запросы согласно доке апи */}
				<DateRangePickerSinceOrder />
				<DateRangePickerUntilOrder />
			</Box>
			{/* Текстовые поля для имени и клиента */}
			<div className='w-2/3 grid grid-cols-2 gap-4'>
				<div className='col-span-1'>
					<Search
						nameQueryParams='name'
						label='Название'
					/>
				</div>
				<div className='col-span-1'>
					<Search
						nameQueryParams='client'
						label='Номенклатура'
					/>
				</div>
				<div className='col-span-1'>
					<StatusOrderFilters />
				</div>
				<div className='col-span-1'>
					{activeTab === 0 && <OrderTypeFilter />}
					{activeTab === 1 && <BrcTypeFilter />}
				</div>
			</div>
			{/* </Paper>
				</Box> */}
			{/* )} */}
		</Box>
	)
}

export default FiltersPanel
