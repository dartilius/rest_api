import NomenclatureDetailWrapper from '@/components/nomenclatures/NomenclatureDetailWrapper'

interface Props {
	params: {
		id: string
	}
}

export default async function NomenclatureDetail({ params }: Props) {
	const { id } = await params

	return (
		<div className='container mx-auto p-4'>
			<NomenclatureDetailWrapper id={id} />
		</div>
	)
}
