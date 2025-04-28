'use client'
import { useDebounce } from '@/hooks/useDebounce'
import {
	Autocomplete,
	Checkbox,
	Chip,
	CircularProgress,
	TextField,
	Box,
	Typography,
} from '@mui/material'
import { useCallback, useEffect, useState } from 'react'

export interface PaginatedResponse<T> {
	results: T[]
	count: number
	next: string | null
}

interface AsyncAutocompleteProps<T> {
	loadOptions: (params: {
		page: number
		search: string
		id?: string
		limit?: number
	}) => Promise<PaginatedResponse<T>>
	value: T[]
	onChange: (value: T[]) => void
	label: string
	multiple?: boolean
	getOptionLabel: (option: T) => string
	isOptionEqualToValue: (option: T, value: T) => boolean
	helperText?: string
}

const AsyncAutocomplete = <T,>({
	loadOptions,
	value,
	onChange,
	label,
	multiple = false,
	getOptionLabel,
	isOptionEqualToValue,
	helperText,
}: AsyncAutocompleteProps<T>) => {
	const [inputValue, setInputValue] = useState<string>('')
	const debouncedSearch = useDebounce(inputValue, 500)
	const [options, setOptions] = useState<T[]>([])
	const [loading, setLoading] = useState<boolean>(false)
	const [pagination, setPagination] = useState({ page: 1, hasMore: true })
	const [isOpen, setIsOpen] = useState<boolean>(false)
	const loadData = useCallback(
		async (page: number, search: string, reset: boolean = false) => {
			try {
				setLoading(true)
				const response = await loadOptions({
					page,
					search,
					limit: 25,
				})

				setOptions((prev) => (reset ? response.results : [...prev, ...response.results]))

				setPagination({
					page,
					hasMore: !!response.next,
				})
			} catch (error) {
				console.error('Error loading options:', error)
			} finally {
				setLoading(false)
			}
		},
		[loadOptions],
	)

	useEffect(() => {
		if (isOpen && debouncedSearch !== null) {
			loadData(1, debouncedSearch, true)
		}
	}, [debouncedSearch, isOpen, loadData])

	const handleScroll = useCallback(
		async (event: React.UIEvent<HTMLElement>) => {
			const { scrollTop, scrollHeight, clientHeight } = event.currentTarget
			if (scrollHeight - scrollTop <= clientHeight + 100 && pagination.hasMore && !loading) {
				await loadData(pagination.page + 1, debouncedSearch)
			}
		},
		[pagination, debouncedSearch, loading, loadData],
	)

	return (
		<Autocomplete
			onOpen={() => setIsOpen(true)}
			onClose={() => setIsOpen(false)}
			multiple={multiple}
			options={options}
			getOptionLabel={getOptionLabel}
			value={value}
			onChange={(_, newValue) => onChange(newValue as T[])}
			onInputChange={(_, value) => setInputValue(value)}
			isOptionEqualToValue={isOptionEqualToValue}
			loading={loading}
			filterOptions={(x) => x}
			noOptionsText={loading ? 'Загрузка...' : 'Ничего не найдено'}
			slotProps={{
				listbox: {
					onScroll: handleScroll,
					style: { maxHeight: 300, overflow: 'auto' },
				},
			}}
			renderInput={(params) => (
				<TextField
					{...params}
					label={label}
					helperText={helperText}
					slotProps={{
						root: {
							// Для кастомизации корневого элемента TextField
						},
						htmlInput: {
							...params.inputProps,
							endadornment: (
								<>
									{loading && (
										<CircularProgress
											color='inherit'
											size={20}
											sx={{ position: 'absolute', right: 50 }}
										/>
									)}
									{params.InputProps.endAdornment}
								</>
							),
						},
					}}
				/>
			)}
			renderTags={(value, getTagProps) =>
				value.map((option, index) => (
					<Chip
						{...getTagProps({ index })}
						key={getOptionLabel(option)}
						label={getOptionLabel(option)}
					/>
				))
			}
			renderOption={(props, option, { selected }) => {
				const { key, ...restProps } = props as { key: React.Key }
				return (
					<li
						key={key}
						{...restProps}
					>
						<Box
							display='flex'
							justifyContent='space-between'
							alignItems='center'
							width='100%'
							sx={{
								'&:hover': {
									backgroundColor: 'rgba(141, 202, 246, 0.3)',
									cursor: 'pointer',
								},
								padding: '8px 16px',
							}}
						>
							<Typography>{getOptionLabel(option)}</Typography>
							{multiple && <Checkbox checked={selected} />}
						</Box>
					</li>
				)
			}}
		/>
	)
}

export default AsyncAutocomplete
