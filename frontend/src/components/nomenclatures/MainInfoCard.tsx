import { INomenclatureResponse } from '@/types/nomeclaturesType'
import { Name } from '@/components/data-display/Name'
import { Description } from '@/components/data-display/Description'

interface IMainInfoCard {
	mainInfo: INomenclatureResponse['main_info']
	className?: string
}

function MainInfoCard({ mainInfo, className }: IMainInfoCard) {
	return (
		<div className={`max-h-[400px] overflow-auto${className}`}>
			<div
				className={`font-bold text-xl md:text-2xl ${
					mainInfo.status === 0 ? 'text-amber-300' : 'text-zinc-200'
				} drop-shadow-[0_1px_2px_rgba(0,0,0,0.4)]`}
			>
				{mainInfo.name}
			</div>
			{mainInfo.status === 0 ? (
				<div className='flex gap-1 md:gap-3 items-baseline text-center'>
					<Name name='Статус:' />
					<Description
						description='Онлайн'
						className='text-emerald-400 drop-shadow-[0_1px_2px_rgba(0,0,0,0.4)] uppercase'
					/>
				</div>
			) : (
				<div className='flex gap-1 md:gap-3 items-baseline text-center'>
					<Name name='Время последнего ответа:' />
					<Description
						description={mainInfo.last_answer}
						className='text-red-400 drop-shadow-[0_1px_2px_rgba(0,0,0,0.4)]'
					/>
				</div>
			)}

			<div className='flex items-baseline gap-1 md:gap-3'>
				<Name name='Дата создания:' />
				<Description
					description={mainInfo.created}
					className='text-gray-100'
				/>
			</div>

			<div className='flex gap-1 md:gap-3 items-baseline text-center'>
				<Name name='Описание:' />
				<Description
					description={mainInfo.description}
					className='text-base text-pink-100'
				/>
			</div>

			<div className='flex gap-1 md:gap-3 items-baseline text-center'>
				<Name name='Владелец:' />
				<Description
					description={mainInfo.owner.full_name}
					className='text-base text-indigo-100'
				/>
			</div>

			<div className='flex gap-1 md:gap-3 items-baseline text-center'>
				<Name name='Часовой пояс:' />
				<Description
					description={mainInfo.timezone}
					className='text-base text-violet-200'
				/>
			</div>

			<div className='flex gap-1 md:gap-3 items-baseline text-center'>
				<Name name='Версия:' />
				<Description
					description={mainInfo.version}
					className='text-base text-lime-200'
				/>
			</div>
		</div>
	)
}

export default MainInfoCard
