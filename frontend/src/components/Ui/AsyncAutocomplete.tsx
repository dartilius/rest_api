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
	isOptionEqualToValue?: (option: T, value: T) => boolean
	helperText?: string
}

const AsyncAutocomplete = <T,>({
	loadOptions,
	value,
	onChange,
	label,
	multiple = false,
	getOptionLabel,
	isOptionEqualToValue = (option, val) => option === val,
	helperText,
}: AsyncAutocompleteProps<T>) => {
	const [inputValue, setInputValue] = useState<string>('')
	const debouncedSearch = useDebounce(inputValue, 500)
	const [options, setOptions] = useState<T[]>([])
	const [loading, setLoading] = useState(false)
	const [page, setPage] = useState(1)
	const [totalCount, setTotalCount] = useState(0)
	const [isOpen, setIsOpen] = useState(false)

	const hasMore = options.length < totalCount

	const loadData = useCallback(
		async (pageNumber: number, search: string, reset: boolean = false) => {
			try {
				setLoading(true)
				const response = await loadOptions({
					page: pageNumber,
					search,
					limit: 25,
				})

				setOptions((prev) => (reset ? response.results : [...prev, ...response.results]))

				setTotalCount(response.count)

				// Всегда обновляем номер страницы после успешной загрузки
				if (!reset) {
					setPage(pageNumber)
				} else {
					setPage(1) // Сбрасываем страницу при поиске/открытии
				}
			} catch (error) {
				console.error('Error loading options:', error)
			} finally {
				setLoading(false)
			}
		},
		[loadOptions],
	)

	useEffect(() => {
		if (isOpen || debouncedSearch !== '') {
			// При изменении поиска или открытии списка:
			// 1. Сбрасываем страницу
			// 2. Загружаем с первой страницы
			// 3. Полностью заменяем данные (reset=true)
			loadData(1, debouncedSearch, true)
		}
	}, [debouncedSearch, isOpen])

	const handleScroll = useCallback(
		async (event: React.UIEvent<HTMLElement>) => {
			const { scrollTop, scrollHeight, clientHeight } = event.currentTarget
			const isNearBottom = scrollHeight - scrollTop <= clientHeight + 100

			if (isNearBottom && hasMore && !loading) {
				// Всегда запрашиваем следующую страницу
				const nextPage = page + 1
				await loadData(nextPage, debouncedSearch)
			}
		},
		[hasMore, loading, debouncedSearch, page, loadData],
	)
	const autocompleteValue = multiple ? value : value.length > 0 ? value[0] : null

	return (
		<Autocomplete
			onOpen={() => setIsOpen(true)}
			onClose={() => setIsOpen(false)}
			multiple={multiple}
			options={options}
			getOptionLabel={(option) => {
				if (option === null || option === undefined) return ''
				return getOptionLabel(option)
			}}
			onInputChange={(_, value) => setInputValue(value)}
			value={autocompleteValue}
			onChange={(_, newValue) => {
				if (multiple) {
					onChange(newValue as T[])
				} else {
					onChange(newValue ? [newValue as T] : [])
				}
			}}
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
				multiple &&
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
