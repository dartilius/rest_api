'use client'

import { StatusSelect } from '@/components/nomenclatures/Status/StatusSelect'
import { TimezoneSelect } from '@/components/nomenclatures/TimeZone/TimezoneSelect'
import ActionButton from '@/components/Ui/button/ActionButton'
import FilterListIcon from '@mui/icons-material/FilterList'
import { useState } from 'react'
import { CreateNomenclature } from '../CreateNomenclature/CreateNomenclature'
import { Search } from '../Search/Search'
import { VersionSelect } from '../Version/VersionSelect'
export default function FiltersMobile() {
	const [openFilters, setOpenFilters] = useState<boolean>(false)

	return (
		<>
			<div className='flex flex-row gap-2 w-full p-4 justify-between'>
				<ActionButton
					icon={FilterListIcon}
					onClick={() => setOpenFilters(!openFilters)}
				>
					Фильтры
				</ActionButton>
				<CreateNomenclature />
			</div>
			{openFilters && (
				<div className='flex flex-col gap-2 mb-2'>
					<Search
						nameQueryParams='name'
						label='Название'
					/>
					<VersionSelect />
					<StatusSelect />
					<TimezoneSelect />
				</div>
			)}
		</>
	)
}
