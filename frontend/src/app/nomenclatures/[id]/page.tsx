import { getNomenclatureDetail } from '@/services/NomenclaturesService'
import NomenclatureDetailCard from '@/components/nomenclatures/NomenclatureDetailCard'

interface Props {
	params: {
		id: string
	}
}

export default async function NomenclatureDetail({ params }: Props) {
	const { id } = await new Promise<{ id: string }>((resolve) => resolve(params))

	try {
		const res = await getNomenclatureDetail(id)
		console.log(res)
		return (
			<div className='container mx-auto p-4'>
				<NomenclatureDetailCard data={res} />
			</div>
		)
	} catch (error) {
		console.error('Error loading Nomenclature details:', error)
		return (
			<div className='container mx-auto p-4 text-red-500'>Ошибка загрузки деталей номенклатуры</div>
		)
	}
}
