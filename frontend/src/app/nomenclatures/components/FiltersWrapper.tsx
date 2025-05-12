'use client'

import { Search } from '@/app/nomenclatures/components/Search/Search'
import { VersionSelect } from '@/app/nomenclatures/components/Version/VersionSelect'
import { StatusSelect } from '@/app/nomenclatures/components/Status/StatusSelect'
import { TimezoneSelect } from '@/app/nomenclatures/components/TimeZone/TimezoneSelect'
import CreateNomenclature from '@/app/nomenclatures/components/CreateNomenclature/CreateNomenclature'

export const FiltersWrapper = () => {
	return (
		<div className='flex flex-row gap-2 w-full p-4'>
			<Search
				nameQueryParams='name'
				label='Название'
			/>
			<VersionSelect />
			<StatusSelect />
			<TimezoneSelect />
			<CreateNomenclature />
		</div>
	)
}
