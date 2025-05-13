'use client'

import { getNomenclatureStatistics } from '@/app/nomenclatures/api'
import { useState, useEffect } from 'react'

export default function ResponseStatistics({ id }: { id: string }) {
	const [statistics, setStatistics] = useState<any>(null)

	useEffect(() => {
		const fetchStatistics = async () => {
			const res = await getNomenclatureStatistics(id)
			setStatistics(res)
		}
		fetchStatistics()
	}, [id])

	console.log('statistics', statistics)
	return <div></div>
}
