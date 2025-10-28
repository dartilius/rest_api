import { ModalAddFile } from '@/app/files/components/ModalAddFile/ModalAddFile'
import SelectTagsFilterWrapper from '@/app/files/components/SelectTags/SelectTagsFilterWrapper'
import SelectType from '@/app/files/components/SelectType/SelectType'
import { Search } from '@/components/nomenclatures'
import ActionButton from '@/components/Ui/button/ActionButton'
import FilterListIcon from '@mui/icons-material/FilterList'
import { Theme, useMediaQuery } from '@mui/material'
import { useState } from 'react'

const FiltersWrapper = () => {
	const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down('md'))
	const [showFilters, setShowFilters] = useState(false)

	return (
		<div className={`flex ${isMobile ? 'flex-col' : 'flex-row'} gap-2 w-full p-4`}>
			{isMobile ? (
				<>
					<div className='flex flex-row gap-2 w-full'>
						<ActionButton
							variant='transparent'
							icon={FilterListIcon}
							onClick={() => setShowFilters(!showFilters)}
						>
							Фильтры
						</ActionButton>
						<ModalAddFile />
					</div>
					{showFilters && (
						<div className='flex flex-col gap-2 w-full'>
							<Search
								nameQueryParams='name'
								label='Название'
							/>
							<div className='flex flex-row gap-2 w-full'>
								<SelectType />
								<SelectTagsFilterWrapper />
							</div>
						</div>
					)}
				</>
			) : (
				<div className='flex flex-row gap-2 w-full'>
					<Search
						nameQueryParams='name'
						label='Название'
					/>
					<SelectType />
					<SelectTagsFilterWrapper />
					<ModalAddFile />
				</div>
			)}
		</div>
	)
}

export default FiltersWrapper
