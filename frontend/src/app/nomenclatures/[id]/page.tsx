import { NomenclatureDetailCard } from '@/components/nomenclatures/NomenclatureDetailCard'
import { Metadata, ResolvingMetadata } from 'next'
import { getNomenclatureDetail } from '../api'
interface Props {
	params: {
		id: string
	}
}

export async function generateMetadata(
	{ params }: Props,
	parent: ResolvingMetadata,
): Promise<Metadata> {
	const { id } = await new Promise<{ id: string }>((resolve) => resolve(params))

	const res = await getNomenclatureDetail(id)

	return {
		title: res.main_info.name,
		description: res.main_info.description,
	}
}

export default async function NomenclatureDetail({ params }: Props) {
	const { id } = await new Promise<{ id: string }>((resolve) => resolve(params))

	try {
		const res = await getNomenclatureDetail(id)

		return (
			<div className='container mx-auto p-4'>
				<NomenclatureDetailCard
					data={res}
					className={`custom_scroll`}
				/>
			</div>
		)
	} catch (error) {
		console.error('Error loading Nomenclature details:', error)
		return (
			<div className='container mx-auto p-4 text-red-500'>Ошибка загрузки деталей номенклатуры</div>
		)
	}
}
