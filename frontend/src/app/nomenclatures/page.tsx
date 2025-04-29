import { TableNomenclatures } from '@/app/nomenclatures/components'
import { Metadata } from 'next'
import { getNomenclatureList } from './api'

export const metadata: Metadata = {
	title: 'Номенклатуры',
	description: 'Страница со списком номенклатур',
	icons: {
		icon: '/favicon.svg',
	},
}
const Nomenclatures = async ({
	searchParams,
}: {
	searchParams?: {
		page: number
		limit: number
		name: string
		status: string
		timezone: string
		version: string
	}
}) => {
	const {
		page = 1,
		limit = 10,
		name = '',
		status = '',
		timezone = '',
		version = '',
	} = (await searchParams) ?? {}

	const listNomenclature = await getNomenclatureList({
		limit,
		name,
		page,
		status,
		timezone,
		version,
	})

	return (
		<div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
			<TableNomenclatures
				count={listNomenclature.count}
				data={listNomenclature.results}
				limit={limit}
				page={page}
			/>
		</div>
	)
}

export default Nomenclatures
