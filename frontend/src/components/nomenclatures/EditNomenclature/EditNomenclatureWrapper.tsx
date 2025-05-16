'use client'
import { INomenclatureResponse } from '@/types/nomeclaturesType'
import { useEffect, useRef, useState } from 'react'
import { getNomenclatureDetail } from '../../../app/nomenclatures/api'
import { EditNomenclature } from './EditNomenclature'

interface EditNomenclatureProps {
	id: string
	open: boolean
	onClose: (e?: React.MouseEvent<Element, MouseEvent>) => void
}

export function EditNomenclatureWrapper({ id, open, onClose }: EditNomenclatureProps) {
	const [data, setData] = useState<INomenclatureResponse>({
		id: '',
		article: '',
		hw_info: {
			audiodevices: [],
			interfaces: [],
			model: '',
			revision: '',
			serial_number: '',
			sd_card_data: {
				manf_id: '',
				name: '',
			},
		},
		main_info: {
			created: '',
			description: '',
			last_answer: '',
			name: '',
			owner: {
				full_name: '',
			},
			status: 0,
			timezone: '',
			version: '',
		},
		settings: {},
	})
	const [error, setError] = useState<Error | null>(null)
	const isFirstRender = useRef(true)

	useEffect(() => {
		if (isFirstRender.current) {
			isFirstRender.current = false
			async function fetchData() {
				try {
					const res = await getNomenclatureDetail(id)
					setData(res)
				} catch (err) {
					setError(err instanceof Error ? err : new Error('Unknown error occurred'))
				}
			}
			fetchData()
		}
	}, [id])

	if (error) {
		return (
			<div className='container mx-auto p-4 text-red-500'>Ошибка загрузки деталей номенклатуры</div>
		)
	}

	const handleClose = (e?: React.MouseEvent<Element, MouseEvent>) => {
		onClose(e)
	}

	return (
		<EditNomenclature
			id={id}
			openModal={open}
			onClose={handleClose}
			data={data}
		/>
	)
}
