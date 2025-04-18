import { INomenclatureResponse } from '@/types/nomeclaturesType'

interface ISettingsInfoCard {
	settingsInfo: INomenclatureResponse['settings']
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

function SettingsInfoCard({ settingsInfo }: ISettingsInfoCard) {
	return (
        <div>
            {DAYS_OF_WEEK.map((day) => (
                <div key={day.id}>
                    {day.name}{' '}{settingsInfo[day.key].worktime}
                </div>
            ))}
        </div>
    )
}

export default SettingsInfoCard
