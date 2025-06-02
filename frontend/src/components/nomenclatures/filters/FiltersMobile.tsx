'use client'

import { StatusSelect } from '@/components/nomenclatures/Status/StatusSelect'
import { TimezoneSelect } from '@/components/nomenclatures/TimeZone/TimezoneSelect'
import ActionButton from '@/components/Ui/button/ActionButton'
import FilterListIcon from '@mui/icons-material/FilterList'
import { useState } from 'react'
import { CreateNomenclature } from '../CreateNomenclature/CreateNomenclature'
import { Search } from '../Search/Search'
import { VersionSelect } from '../Version/VersionSelect'
import { AppBar, Box, IconButton, Typography } from '@mui/material'
export default function FiltersMobile() {
	const [openFilters, setOpenFilters] = useState<boolean>(false)

	return (
		<>
			<AppBar
				position='sticky'
				sx={{
					// zIndex: (theme) => theme.zIndex.drawer + 1,
					display: 'flex',
					flexDirection: 'row',
					p: 1,
					justifyContent: 'center',
					// width: '100%',
					// height: '100%',
					top: 0,
					gap: 4,
					backgroundColor: 'background.paper',
				}}
				// className='flex flex-row gap-4 w-full h-full p-2 justify-center'
			>
				<Box
					display='flex'
					width='100%'
					height={'100%'}
					justifyContent='center'
					alignItems='center'
				>
					<IconButton
						onClick={() => setOpenFilters(!openFilters)}
						color='primary'
						// sx={{ p: 0 }}
					>
						<FilterListIcon fontSize='large' />
					</IconButton>
					<Box
						sx={{
							display: 'flex',
							justifyContent: 'center',
							alignItems: 'center',
							width: '100%', // Занимает всю доступную ширину
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
							Номенклатура
						</Typography>
					</Box>
					<CreateNomenclature />
				</Box>
			</AppBar>
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
