import { INomenclatureResponse } from '@/types/nomeclaturesType'
import { Name } from '@/components/data-display/Name'
import { Description } from '@/components/data-display/Description'

interface ISettingsInfoCard {
	settingsInfo: INomenclatureResponse['settings']
	className?: string
}

const DAYS_OF_WEEK = [
	{ id: 0, name: 'Пн', key: 'mon' },
	{ id: 1, name: 'Вт', key: 'tue' },
	{ id: 2, name: 'Ср', key: 'wed' },
	{ id: 3, name: 'Чт', key: 'thu' },
	{ id: 4, name: 'Пт', key: 'fri' },
	{ id: 5, name: 'Сб', key: 'sat' },
	{ id: 6, name: 'Вс', key: 'sun' },
]

function SettingsInfoCard({ settingsInfo, className }: ISettingsInfoCard) {
	return (
		<div className={`${className}`}>
			<Name
				name='Настройки'
				className={`font-bold text-2xl text-zinc-100 drop-shadow-[0_1px_2px_rgba(0,0,0,0.4)]`}
			/>
			{DAYS_OF_WEEK.map((day) => (
				<div
					key={day.id}
					className='flex items-baseline text-center gap-3'
				>
					<Name
						name={`${day.name}:`}
						className='font-bold text-lg leading-[1.2]'
					/>
					<Description
						description={settingsInfo[day.key].worktime}
						className='text-base leading-[1.2]'
					/>
				</div>
			))}
		</div>
	)
}

export default SettingsInfoCard
