'use client'
import { convertStatus } from '@/types/checkStatus'
import { FormControl, MenuItem, Select } from '@mui/material'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { handleQueryParamChange } from '@/utils'

export const StatusSelect = () => {
	const statusTypes = [0, 1, 2, 3]
	const router = useRouter()
	const pathname = usePathname()
	const searchParams = useSearchParams()
	const currentStatus = searchParams.get('status') || ''
	const [status, setStatus] = useState<string>(currentStatus)

	useEffect(() => {
		setStatus(currentStatus)
	}, [currentStatus])

	const handleStatusChange = (value: string) => {
		handleQueryParamChange(router, pathname, searchParams, 'status', value)
	}

	return (
		<FormControl fullWidth>
			<Select
				value={status}
				onChange={(event) => handleStatusChange(event.target.value as string)}
				style={{ color: 'black', backgroundColor: 'white', borderRadius: '4px' }}
				displayEmpty
				renderValue={(value) => {
					if (!value) return 'Выберите статус номенклатуры'
					return convertStatus(Number(value))
				}}
			>
				{statusTypes.map((item) => (
					<MenuItem
						key={item}
						value={item.toString()}
					>
						{convertStatus(item)}
					</MenuItem>
				))}
			</Select>
		</FormControl>
	)
}
