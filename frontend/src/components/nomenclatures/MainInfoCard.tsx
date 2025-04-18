import { INomenclatureResponse } from '@/types/nomeclaturesType'

interface IMainInfoCard {
	mainInfo: INomenclatureResponse['main_info']
	className?: string
}
/*
Tailwind класс | Визуальное ощущение | Почему подойдёт?
text-amber-300 | Золотистый акцент | Теплый контраст, ощущение премиум
text-cyan-300 | Неоновый бирюзовый | Энергия, техно-стиль
text-lime-300 | Неоновый лайм | Привлекает внимание сразу
text-zinc-200 | Холодный светло-серый | Подчёркивает современность
*/

function MainInfoCard({ mainInfo, className }: IMainInfoCard) {
	return (
		<div className={`${className}`}>
			<div className={`font-bold text-2xl ${mainInfo.status === 0 ? 'text-amber-300' : 'text-zinc-200' }  drop-shadow-[0_1px_2px_rgba(0,0,0,0.4)]`}>
				{mainInfo.name}
			</div>
			{mainInfo.status === 0 ? (
				<div className='flex flex-row gap-3 items-center text-center'>
					<div className='font-bold text-lg leading-[1.2]'>Статус:</div>
					<div className='text-base leading-[1.2] text-emerald-400 drop-shadow-[0_1px_2px_rgba(0,0,0,0.4)]'>Онлайн</div>
				</div>
			) : (
				<div className='flex flex-row gap-3'>
					<div className='font-bold text-lg leading-[1.2]'>Время последнего ответа:</div>
					<div className='text-base leading-[1.2] text-red-400 drop-shadow-[0_1px_2px_rgba(0,0,0,0.4)]'>{mainInfo.last_answer}</div>
				</div>
			)}
			<div className='flex flex-row gap-3'>
				<div className='font-bold text-lg leading-[1.2]'>Дата создания:</div>
				<div className='text-base leading-[1.2]'>{mainInfo.created}</div>
			</div>
			<div className='flex flex-row gap-3'>
				<div className='font-bold text-lg leading-[1.2]'>Описание:</div>
				<div className='text-base leading-[1.2]'>{mainInfo.description}</div>
			</div>
			<div className='flex flex-row gap-3'>
				<div className='font-bold text-lg leading-[1.2]'>Владелец:</div>
				<div className='text-base leading-[1.2]'>{mainInfo.owner.full_name}</div>
			</div>
			<div className='flex flex-row gap-3'>
				<div className='font-bold text-lg leading-[1.2]'>Часовой пояс:</div>
				<div className='text-base leading-[1.2]'>{mainInfo.timezone}</div>
			</div>
			<div className='flex flex-row gap-3'>
				<div className='font-bold text-lg leading-[1.2]'>Версия:</div>
				<div className='text-base leading-[1.2]'>{mainInfo.version}</div>
			</div>
		</div>
	)
}

export default MainInfoCard
