import { Description } from '@/components/data-display/Description'
import { Name } from '@/components/data-display/Name'
import { INomenclatureResponse } from '@/types/nomeclaturesType'

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

export function SettingsInfoCard({ settingsInfo, className }: ISettingsInfoCard) {
	const formatVolume = (volume: number[]) => {
		return `[${volume.join(', ')}]`
	}

	const formatCustomVolume = (customVolume?: { [key: string]: number[] }) => {
		if (!customVolume || Object.keys(customVolume).length === 0) {
			return (
				<Description
					description='Не настроено'
					className='text-sm text-zinc-500 italic'
				/>
			)
		}
		return Object.entries(customVolume).map(([timeRange, volume]) => (
			<div
				key={timeRange}
				className='text-sm'
			>
				<Description
					description={`${timeRange}: ${formatVolume(volume)}`}
					className='text-zinc-400'
				/>
			</div>
		))
	}

	return (
		<div className={`${className}`}>
			<div className='grid gap-4'>
				{DAYS_OF_WEEK.map((day) => (
					<div
						key={day.id}
						className='bg-white/5 rounded-lg p-4 w-full overflow-hidden'
					>
						<div className='flex items-center justify-between flex-wrap gap-2'>
							<Name
								name={day.name}
								className='font-bold text-lg'
							/>
							<Description
								description={settingsInfo[day.key].worktime}
								className='text-zinc-300 break-all'
							/>
						</div>
						<div className='flex flex-col gap-1'>
							<div className='flex gap-1 items-baseline flex-wrap'>
								<Name
									className='text-zinc-400'
									name='Громкость по умолчанию:'
								/>
								<Description
									description={formatVolume(settingsInfo[day.key].default_volume)}
									className='text-zinc-300 break-all'
								/>
							</div>
							<div className='flex gap-1 items-baseline flex-wrap'>
								<Name
									className='text-zinc-400'
									name='Настраиваемая громкость:'
								/>
								{formatCustomVolume(settingsInfo[day.key].custom_volume)}
							</div>
						</div>
					</div>
				))}
			</div>
		</div>
	)
}
