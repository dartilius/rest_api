'use client'
import { useEffect, useState } from 'react'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import Autocomplete from '@mui/material/Autocomplete'
import TextField from '@mui/material/TextField'
import Checkbox from '@mui/material/Checkbox'
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank'
import CheckBoxIcon from '@mui/icons-material/CheckBox'
import { useStore } from '@/providers/mobx-provider/MobxProvider'
import { handleQueryParamChange } from '@/utils'
import { OrderStatus } from '@/types/orderTypes'

const icon = <CheckBoxOutlineBlankIcon fontSize='small' />
const checkedIcon = <CheckBoxIcon fontSize='small' />

const STATUS_OPTIONS = Object.entries(OrderStatus)
	.filter(([key]) => isNaN(Number(key)))
	.map(([_key, value]) => ({
		queryParams: String(value),
		label: {
			[OrderStatus.PENDING]: 'В ожидании',
			[OrderStatus.LIVE]: 'В эфире',
			[OrderStatus.COMPLETED]: 'Завершено',
			[OrderStatus.CANCELLED]: 'Отменён',
			[OrderStatus.ERROR]: 'Ошибка',
		}[value as OrderStatus],
	}))

export function StatusOrderFilters() {
	const { ordersStore } = useStore()
	const searchParams = useSearchParams()
	const pathname = usePathname()
	const router = useRouter()
	const currentValue = searchParams?.get('status') || ''
	const [selectedValue, setSelectedValue] = useState<string>(currentValue)

	useEffect(() => {
		setSelectedValue(currentValue)
	}, [currentValue])

	const handleChange = (_: any, newValue: { queryParams: string; label: string } | null) => {
		const value = newValue?.queryParams || ''
		setSelectedValue(value)
		handleQueryParamChange(router, pathname, searchParams, 'status', value)
		ordersStore.setPage(1)
	}

	return (
		<Autocomplete
			size='small'
			fullWidth
			options={STATUS_OPTIONS}
			getOptionLabel={(option) => option.label}
			disableCloseOnSelect
			value={STATUS_OPTIONS.find((option) => option.queryParams === selectedValue) || null}
			onChange={handleChange}
			renderOption={(props, option, { selected }) => {
				const { key, ...restProps } = props as {
					key: React.Key
				} & React.HTMLAttributes<HTMLLIElement>

				return (
					<li
						key={key}
						{...restProps}
					>
						<Checkbox
							icon={icon}
							checkedIcon={checkedIcon}
							style={{ marginRight: 8 }}
							checked={selected}
						/>
						{option.label}
					</li>
				)
			}}
			renderInput={(params) => (
				<TextField
					{...params}
					label='Статус'
				/>
			)}
		/>
	)
}
