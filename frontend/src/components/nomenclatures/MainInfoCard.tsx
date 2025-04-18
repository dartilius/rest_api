import { INomenclatureResponse } from '@/types/nomeclaturesType'
import {Name} from "@/components/data-display/Name";
import {Description} from "@/components/data-display/Description";

interface IMainInfoCard {
	mainInfo: INomenclatureResponse['main_info']
	className?: string
}

function MainInfoCard({ mainInfo, className }: IMainInfoCard) {
	return (
		<div className={`${className}`}>
			{/*<div*/}
			{/*	className={`font-bold text-2xl ${*/}
			{/*		mainInfo.status === 0 ? 'text-amber-300' : 'text-zinc-200'*/}
			{/*	} drop-shadow-[0_1px_2px_rgba(0,0,0,0.4)]`}*/}
			{/*>*/}
			{/*{mainInfo.name}*/}
			<Name
				name={mainInfo.name}
				className={`font-bold text-2xl ${
					mainInfo.status === 0 ? 'text-amber-300' : 'text-zinc-200'
				} drop-shadow-[0_1px_2px_rgba(0,0,0,0.4)]`}
			/>
			{/*</div>*/}

			{mainInfo.status === 0 ? (
				<div className='flex gap-3 items-baseline text-center'>
					<Name name='Статус: ' className='font-bold text-lg leading-[1.2]'/>
					<Name name='Онлайн ' className='text-xl leading-[1.2] text-emerald-400 drop-shadow-[0_1px_2px_rgba(0,0,0,0.4)]'/>
				</div>
			) : (
				<div className='flex gap-3 items-baseline text-center'>
					<Name name='Время последнего ответа: ' className='font-bold text-lg leading-[1.2]'/>
					<Name name={mainInfo.last_answer} className='text-xl leading-[1.2] text-red-400 drop-shadow-[0_1px_2px_rgba(0,0,0,0.4)]'/>
				</div>
			)}

			<div className='flex gap-3 items-baseline text-center'>
				<Name name='Дата создания: ' className='font-bold text-lg leading-[1.2]'/>
				<Description description={mainInfo.created} className='text-base leading-[1.2]'/>
			</div>

			<div className='flex gap-3 items-baseline text-center'>
				<Name name='Описание: ' className='font-bold text-lg leading-[1.2]'/>
				<Description description={mainInfo.description} className='text-base leading-[1.2]'/>
			</div>

			<div className='flex gap-3 items-baseline text-center'>
				<Name name='Владелец: ' className='font-bold text-lg leading-[1.2]'/>
				<Description description={mainInfo.owner.full_name} className='text-base leading-[1.2]'/>
			</div>

			<div className='flex gap-3 items-baseline text-center'>
				<Name name='Часовой пояс: ' className='font-bold text-lg leading-[1.2]'/>
				<Description description={mainInfo.timezone} className='text-base leading-[1.2]'/>
			</div>

			<div className='flex gap-3 items-baseline text-center'>
				<Name name='Версия: ' className='font-bold text-lg leading-[1.2]'/>
				<Description description={mainInfo.version} className='text-base leading-[1.2]'/>
			</div>
		</div>
	)
}

export default MainInfoCard
