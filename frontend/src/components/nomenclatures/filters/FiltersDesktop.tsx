import { StatusSelect } from '@/components/nomenclatures/Status/StatusSelect'
import { TimezoneSelect } from '@/components/nomenclatures/TimeZone/TimezoneSelect'
import { CreateNomenclature } from '../CreateNomenclature/CreateNomenclature'
import { Search } from '../Search/Search'
import { VersionSelect } from '../Version/VersionSelect'

export default function FiltersDesktop() {
	return (
		<div className='flex flex-row gap-2 w-full p-4'>
			<Search
				nameQueryParams='name'
				label='Название'
			/>
			<VersionSelect />
			<StatusSelect />
			<TimezoneSelect />
			<div className='m-auto'>
				<CreateNomenclature />
			</div>
		</div>
	)
}
