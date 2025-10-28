'use client'
import { useStore } from '@/providers/mobx-provider/MobxProvider'
import { handleQueryParamChange } from '@/utils'
import { TextField } from '@mui/material'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { ChangeEvent, useEffect, useState } from 'react'
import { useDebouncedCallback } from 'use-debounce'
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
			size='medium'
			style={{ backgroundColor: 'white', borderRadius: '4px', width: '100%' }}
		/>
	)
}
