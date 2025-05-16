import { TableNomenclatures } from '@/components/nomenclatures'
import { Metadata } from 'next'
import { getNomenclatureList } from './api'

export const metadata: Metadata = {
	title: 'Номенклатуры',
	description: 'Страница со списком номенклатур',
	icons: {
		icon: '/favicon.svg',
	},
}
const NomenclaturesPage = async ({
	searchParams,
}: {
	searchParams?: {
		name: string
		page: number
		limit: number
		version: string
		status: string
		timezone: string
	}
}) => {
	const {
		page = 1,
		limit = 20,
		name = '',
		version = '',
		status = '',
		timezone = '',
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
		<div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', height: '100%' }}>
			<TableNomenclatures
				count={listNomenclature.count}
				data={listNomenclature.results}
				limit={limit}
				page={page}
			/>
		</div>
	)
}

export default NomenclaturesPage
