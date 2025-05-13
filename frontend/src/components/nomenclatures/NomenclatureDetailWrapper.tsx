'use client'

import { useEffect, useState } from 'react'
import { getNomenclatureDetail } from '@/app/nomenclatures/api'
import NomenclatureDetailCard from './NomenclatureDetailCard'
import { INomenclatureResponse } from '@/types/nomeclaturesType'

export default function NomenclatureDetailWrapper({ id }: { id: string }) {
	const [data, setData] = useState<INomenclatureResponse | null>(null)
	const [error, setError] = useState<string | null>(null)

	useEffect(() => {
		const fetchData = async () => {
			try {
				const res = await getNomenclatureDetail(id)
				setData(res)
			} catch (err) {
				setError('Ошибка загрузки деталей номенклатуры')
				console.error('Error loading Nomenclature details:', err)
			}
		}

		fetchData()
	}, [id])

	if (error) {
		return <div className='container mx-auto p-4 text-red-500'>{error}</div>
	}

	if (!data) {
		return <div className='container mx-auto p-4'>Загрузка...</div>
	}

	return <NomenclatureDetailCard data={data} />
}
