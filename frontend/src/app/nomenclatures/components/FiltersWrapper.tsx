'use client'

import { Typography } from '@mui/material'
import { Search } from '@/app/nomenclatures/components/Search/Search'
import { VersionSelect } from '@/app/nomenclatures/components/Version/VersionSelect'
import { StatusSelect } from '@/app/nomenclatures/components/Status/StatusSelect'
import { TimezoneSelect } from '@/app/nomenclatures/components/TimeZone/TimezoneSelect'
import CreateNomenclature from '@/app/nomenclatures/components/CreateNomenclature/CreateNomenclature'

export const FiltersWrapper = () => {
	return (
		<div className='flex flex-row gap-2 w-full p-4'>
			<div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
				<Typography variant='subtitle1'>Поиск</Typography>
				<Search
					nameQueryParams='name'
					label='Название'
				/>
			</div>
			<div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
				<Typography variant='subtitle1'>Версия</Typography>
				<VersionSelect />
			</div>
			<div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
				<Typography variant='subtitle1'>Статус</Typography>
				<StatusSelect />
			</div>
			<div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
				<Typography variant='subtitle1'>Часовой пояс</Typography>
				<TimezoneSelect />
			</div>
			<div
				style={{
					display: 'flex',
					width: '100%',
					justifyContent: 'center',
					alignItems: 'center',
				}}
			>
				<CreateNomenclature />
			</div>
		</div>
	)
}
