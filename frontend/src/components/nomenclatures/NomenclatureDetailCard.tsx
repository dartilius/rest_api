import { INomenclatureResponse } from '@/types/nomeclaturesType'
import MainInfoCard from '@/components/nomenclatures/MainInfoCard'
import SettingsInfoCard from '@/components/nomenclatures/SettingsInfoCard'
import TabsSwitcher from '@/components/nomenclatures/TabsSwitcher'
import HardwareCard from '@/components/nomenclatures/HardwareCard'
import ResponseStatistics from './statistics/ResponseStatistics'

interface INomenclatureDetail {
	data: INomenclatureResponse
	className?: string
}

function NomenclatureDetailCard({ data, className = '' }: INomenclatureDetail) {
	return (
		<div
			className={`bg-gradient-to-r from-purple-700 to-pink-600 rounded-lg shadow p-4 md:p-6 ${className}`}
		>
			<TabsSwitcher
				mainTab={
					<MainInfoCard
						mainInfo={data['main_info']}
						className='bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-500
                                   rounded-lg shadow p-4 md:p-6 gap-3 flex flex-col'
					/>
				}
				settingsTab={
					<SettingsInfoCard
						settingsInfo={data['settings']}
						className='bg-gradient-to-r from-rose-400 via-orange-300 to-yellow-200
             					   rounded-lg shadow p-4 md:p-6 gap-3 flex flex-col'
					/>
				}
				hardwareTab={
					<HardwareCard
						hardwareInfo={data['hw_info']}
						className='bg-gradient-to-r from-purple-500 via-violet-400 to-fuchsia-300
           						   rounded-lg shadow p-4 md:p-6 gap-3 flex flex-col'
					/>
				}
				statisticsTab={<ResponseStatistics />}
			/>
		</div>
	)
}

export default NomenclatureDetailCard
