import { INomenclatureResponse } from '@/types/nomeclaturesType'
import { Name } from '@/components/data-display/Name'
import { Description } from '@/components/data-display/Description'

interface IHardwareCard {
	hardwareInfo: INomenclatureResponse['hw_info']
	className?: string
}

function HardwareCard({ hardwareInfo, className }: IHardwareCard) {
	return (
		<div className={`${className}`}>
			<div className='space-y-2 mb-6'>
				<div className='flex flex-wrap gap-1 md:gap-3 items-baseline'>
					<Name
						name='Модель:'
						className='text-lg'
					/>
					<Description
						description={hardwareInfo.model}
						className='text-base text-emerald-200 break-all'
					/>
				</div>

				<div className='flex flex-wrap gap-1 md:gap-3 items-baseline'>
					<Name
						name='Ревизия:'
						className='text-lg'
					/>
					<Description
						description={hardwareInfo.revision}
						className='text-base text-emerald-200 break-all'
					/>
				</div>

				<div className='flex flex-wrap gap-1 md:gap-3 items-baseline'>
					<Name
						name='Серийный номер:'
						className='text-lg'
					/>
					<Description
						description={hardwareInfo.serial_number}
						className='text-base text-emerald-200 font-mono break-all'
					/>
				</div>
			</div>

			<div className='mb-6'>
				<Name
					name='Сетевые интерфейсы'
					className='text-xl text-zinc-100 drop-shadow-[0_1px_2px_rgba(0,0,0,0.4)] mb-2'
				/>
				<div className='space-y-4'>
					{hardwareInfo.interfaces?.map((iface, index) => (
						<div
							key={index}
							className='pl-4 space-y-1 border-l-2 border-indigo-400'
						>
							<div className='flex flex-wrap gap-1 md:gap-3 items-baseline'>
								<Name
									name='Интерфейс:'
									className='text-lg'
								/>
								<Description
									description={iface.iface}
									className='text-base text-sky-200 break-all'
								/>
							</div>
							<div className='flex flex-wrap gap-1 md:gap-3 items-baseline'>
								<Name
									name='MAC:'
									className='text-lg'
								/>
								<Description
									description={iface.mac}
									className='text-base text-sky-200 font-mono break-all'
								/>
							</div>
							<div className='flex flex-wrap gap-1 md:gap-3 items-baseline'>
								<Name
									name='IP:'
									className='text-lg'
								/>
								<Description
									description={iface.ip}
									className='text-base text-sky-200 font-mono break-all'
								/>
							</div>
						</div>
					))}
				</div>
			</div>

			<div className='mb-6'>
				<Name
					name='Аудио устройства'
					className='text-xl text-zinc-100 drop-shadow-[0_1px_2px_rgba(0,0,0,0.4)] mb-2'
				/>
				<div className='space-y-4'>
					{hardwareInfo.audiodevices?.map((device, index) => (
						<div
							key={index}
							className='pl-4 space-y-1 border-l-2 border-violet-400'
						>
							<div className='flex flex-wrap gap-1 md:gap-3 items-baseline'>
								<Name
									name='Карта:'
									className='text-lg'
								/>
								<Description
									description={device.card.toString()}
									className='text-base text-violet-200 break-all'
								/>
							</div>
							<div className='flex flex-wrap gap-1 md:gap-3 items-baseline'>
								<Name
									name='Название:'
									className='text-lg'
								/>
								<Description
									description={device.name}
									className='text-base text-violet-200 break-all'
								/>
							</div>
						</div>
					))}
				</div>
			</div>

			<div className='mb-4'>
				<Name
					name='SD карта'
					className='text-xl text-zinc-100 drop-shadow-[0_1px_2px_rgba(0,0,0,0.4)] mb-2'
				/>
				<div className='pl-4 space-y-1 border-l-2 border-pink-400'>
					<div className='flex flex-wrap gap-1 md:gap-3 items-baseline'>
						<Name
							name='Название:'
							className='text-lg'
						/>
						<Description
							description={hardwareInfo.sd_card_data?.name}
							className='text-base text-pink-200 break-all'
						/>
					</div>
					<div className='flex flex-wrap gap-1 md:gap-3 items-baseline'>
						<Name
							name='ID производителя:'
							className='text-lg'
						/>
						<Description
							description={hardwareInfo.sd_card_data?.manf_id}
							className='text-base text-pink-200 font-mono break-all'
						/>
					</div>
				</div>
			</div>
		</div>
	)
}

export default HardwareCard
