import { INomenclatureResponse } from '@/types/nomeclaturesType'
import MainInfoCard from '@/components/nomenclatures/MainInfoCard'
import SettingsInfoCard from '@/components/nomenclatures/SettingsInfoCard'
import TabsSwitcher from '@/components/nomenclatures/TabsSwitcher'
import HardwareCard from '@/components/nomenclatures/HardwareCard'
import StatisticsWrapper from './statistics/StatisticsWrapper'

interface INomenclatureDetail {
	data: INomenclatureResponse
	className?: string
}

function NomenclatureDetailCard({ data, className = '' }: INomenclatureDetail) {
	return (
		<div
			className={`bg-gradient-to-r from-blue-950 to-indigo-900 rounded-lg shadow p-2 sm:p-4 md:p-6 ${className}`}
		>
			<TabsSwitcher
				mainTab={
					<MainInfoCard
						mainInfo={data['main_info']}
						className='bg-gradient-to-br from-blue-900 via-indigo-900 to-blue-800
								 rounded-lg shadow p-2 sm:p-4 md:p-6 gap-2 sm:gap-3 flex flex-col overflow-auto'
					/>
				}
				settingsTab={
					<SettingsInfoCard
						settingsInfo={data['settings']}
						className='max-h-[400px] overflow-auto bg-gradient-to-bl from-indigo-900 via-blue-900 to-indigo-800
								 rounded-lg shadow p-2 sm:p-4 md:p-6 gap-2 sm:gap-3 flex flex-col'
					/>
				}
				hardwareTab={
					<HardwareCard
						hardwareInfo={data['hw_info']}
						className='max-h-[400px] overflow-auto bg-gradient-to-tr from-blue-900 via-indigo-900 to-blue-800
								 rounded-lg shadow p-2 sm:p-4 md:p-6 gap-2 sm:gap-3 flex flex-col'
					/>
				}
				statisticsTab={
					<StatisticsWrapper
						id={data.id}
						className='bg-gradient-to-r from-indigo-900 via-blue-900 to-indigo-800 rounded-lg shadow p-2 sm:p-4 md:p-6'
					/>
				}
			/>
		</div>
	)
}

export default NomenclatureDetailCard
