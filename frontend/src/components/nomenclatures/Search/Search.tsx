'use client'
import { ChangeEvent, useEffect, useState } from 'react'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { useDebouncedCallback } from 'use-debounce'
import { TextField } from '@mui/material'
import { handleQueryParamChange } from '@/utils'
import { useStore } from '@/providers/mobx-provider/MobxProvider'
interface IPropsSearch {
	nameQueryParams: string
	label: string
}
export function Search({ ...props }: IPropsSearch) {
	const { nameQueryParams, label } = props
	const { ordersStore } = useStore()
	const searchParams = useSearchParams()
	const pathname = usePathname()
	const router = useRouter()
	const currentSearchValue = searchParams?.get(nameQueryParams) || ''
	const [searchValue, setSearchValue] = useState<string>(currentSearchValue)

	const handleSearch = useDebouncedCallback((value: string) => {
		handleQueryParamChange(router, pathname, searchParams, nameQueryParams, value)
		ordersStore.setPage(1)
	}, 1000)

	useEffect(() => {
		setSearchValue(currentSearchValue)
	}, [currentSearchValue])

	return (
		<TextField
			variant='outlined'
			label={label}
			onChange={(e: ChangeEvent<HTMLInputElement>) => {
				setSearchValue(e.target.value)
				handleSearch(e.target.value)
			}}
			value={searchValue}
			style={{ backgroundColor: 'white', borderRadius: '4px', maxHeight: '52px', width: '100%' }}
		/>
	)
}
