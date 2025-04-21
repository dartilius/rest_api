'use client'

import { createAdOrder, loadClients } from '@/app/adorders/api'
import { getPlayLists } from '@/app/playlists/api'
import { useDebounce } from '@/hooks/useDebounce'
import { AdOrderType, IBroadcastInterval, ORDER_TYPE_AD_CONFIG } from '@/types/orderTypes'
import { IPlayList } from '@/types/playListsTypes'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import {
	Autocomplete,
	Box,
	Button,
	Checkbox,
	Chip,
	CircularProgress,
	Dialog,
	DialogActions,
	DialogContent,
	DialogTitle,
	TextField,
	Typography,
	useMediaQuery,
	useTheme,
} from '@mui/material'
import { DateTimePicker } from '@mui/x-date-pickers'
import dayjs, { Dayjs } from 'dayjs'
import { useRouter } from 'next/navigation'
import { useCallback, useEffect, useState } from 'react'
import ActionButton from '../Ui/button/ActionButton'
import ParametersBlock from './ParametersBlock'

interface Client {
	id: string
	name: string
}

export interface FormState {
	name: string
	description: string
	broadcast_type: AdOrderType
	parameters: {
		weight: number
		times_in_hour: number
		timedelta?: string
		start_time?: string
		end_time?: string
		event?: string
		active_ad?: string
	}
	playlist: IPlayList[]
	clients: Client[]
	broadcast_interval: IBroadcastInterval
}

const CreateAdOrderModal = () => {
	const router = useRouter()
	const theme = useTheme()
	const [open, setOpen] = useState(false)
	const [formData, setFormData] = useState<FormState>({
		name: '',
		description: '',
		broadcast_type: AdOrderType.POINT_TIME,
		parameters: {
			weight: 50,
			times_in_hour: 1,
		},
		playlist: [],
		clients: [],
		broadcast_interval: { lower: '', upper: '' },
	})

	const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
	// Состояния для клиентов
	const [clientsSearch, setClientsSearch] = useState('')
	const debouncedClientsSearch = useDebounce(clientsSearch, 500)
	const [clients, setClients] = useState<Client[]>([])
	const [isLoadingClients, setIsLoadingClients] = useState(false)
	const [clientsPagination, setClientsPagination] = useState({
		page: 1,
		hasMore: true,
		totalCount: 0,
	})

	// Состояния для плейлистов
	const [playlistsSearch, setPlaylistsSearch] = useState('')
	const debouncedPlaylistsSearch = useDebounce(playlistsSearch, 500)
	const [playlists, setPlaylists] = useState<IPlayList[]>([])
	const [isLoadingPlaylists, setIsLoadingPlaylists] = useState(false)
	const [playlistsPagination, setPlaylistsPagination] = useState({
		page: 1,
		hasMore: true,
		totalCount: 0,
	})
	// Загрузка клиентов
	const loadClientsData = useCallback(
		async (page: number, search: string, reset: boolean = false) => {
			try {
				setIsLoadingClients(true)
				const response = await loadClients(page, search)
				setClients((prev) => (reset ? response.results : [...prev, ...response.results]))
				setClientsPagination({
					page,
					hasMore: response.next !== null,
					totalCount: response.count,
				})
			} catch (error) {
				console.error('Failed to load clients:', error)
			} finally {
				setIsLoadingClients(false)
			}
		},
		[],
	)

	// Загрузка плейлистов
	const loadPlaylistsData = useCallback(
		async (page: number, search: string, reset: boolean = false) => {
			try {
				setIsLoadingPlaylists(true)
				const response = await getPlayLists({
					id: '',
					page,
					limit: 25,
					name: search,
				})
				setPlaylists((prev) => (reset ? response.results : [...prev, ...response.results]))
				setPlaylistsPagination({
					page,
					hasMore: response.next !== null,
					totalCount: response.count,
				})
			} catch (error) {
				console.error('Failed to load playlists:', error)
			} finally {
				setIsLoadingPlaylists(false)
			}
		},
		[],
	)

	// Эффекты для загрузки данных
	useEffect(() => {
		let isMounted = true
		const controller = new AbortController()

		const fetchData = async () => {
			if (!isMounted) return
			await loadClientsData(1, debouncedClientsSearch, true)
			await loadPlaylistsData(1, debouncedPlaylistsSearch, true)
		}

		fetchData()
		return () => {
			isMounted = false
			controller.abort()
		}
	}, [debouncedClientsSearch, debouncedPlaylistsSearch])

	// Обработчики скролла
	const handleClientsScroll = useCallback(
		async (event: React.UIEvent<HTMLElement>) => {
			const { scrollTop, scrollHeight, clientHeight } = event.currentTarget
			if (
				scrollHeight - scrollTop <= clientHeight + 100 &&
				clientsPagination.hasMore &&
				!isLoadingClients
			) {
				await loadClientsData(clientsPagination.page + 1, debouncedClientsSearch)
			}
		},
		[
			clientsPagination.hasMore,
			clientsPagination.page,
			debouncedClientsSearch,
			isLoadingClients,
			loadClientsData,
		],
	)

	const handlePlaylistsScroll = useCallback(
		async (event: React.UIEvent<HTMLElement>) => {
			const { scrollTop, scrollHeight, clientHeight } = event.currentTarget
			if (
				scrollHeight - scrollTop <= clientHeight + 100 &&
				playlistsPagination.hasMore &&
				!isLoadingPlaylists
			) {
				await loadPlaylistsData(playlistsPagination.page + 1, debouncedPlaylistsSearch)
			}
		},
		[
			playlistsPagination.hasMore,
			playlistsPagination.page,
			isLoadingPlaylists,
			loadPlaylistsData,
			debouncedPlaylistsSearch,
		],
	)
	const handleDateChange = (field: keyof IBroadcastInterval) => (value: Dayjs | null) => {
		setFormData((prev) => ({
			...prev,
			broadcast_interval: {
				...prev.broadcast_interval,
				[field]: value?.toISOString() || '',
			},
		}))
	}

	const validateForm = () => {
		const errors = []
		if (!formData.name.trim()) errors.push('Название обязательно')
		if (formData.clients.length === 0) errors.push('Выберите клиентов')
		if (!formData.broadcast_interval.lower) errors.push('Укажите начальную дату')
		if (!formData.broadcast_interval.upper) errors.push('Укажите конечную дату')
		return errors
	}

	const handleSubmit = async () => {
		const errors = validateForm()
		if (errors.length > 0) {
			alert(errors.join('\n'))
			return
		}

		try {
			const payload = {
				...formData,
				parameters: {
					...formData.parameters,
					// Конвертация времени при необходимости
					// start_time: formData.parameters.start_time ? `${formData.parameters.start_time}:00` : null,
					// end_time: formData.parameters.end_time ? `${formData.parameters.end_time}:00` : null,
				},
				clients: formData.clients.map((c) => c.id),
				broadcast_interval: {
					lower: formData.broadcast_interval.lower,
					upper: formData.broadcast_interval.upper,
				},
				playlist: formData.playlist.map((v) => v.id),
			}

			await createAdOrder(payload)
			setOpen(false)
			router.refresh()
		} catch (error) {
			console.error('Ошибка создания заказа:', error)
			alert('Ошибка при создании заказа')
		}
	}

	const handleTextChange = (field: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement>) => {
		const value = e.target.value.slice(0, 250)
		setFormData((prev) => ({ ...prev, [field]: value }))
	}

	return (
		<>
			<Box
				display='flex'
				width='20%'
				justifyContent='center'
				alignItems='center'
			>
				<ActionButton
					variant='primary'
					size='lg'
					icon={AddCircleOutlineIcon}
					onClick={() => setOpen(true)}
				>
					Создать
				</ActionButton>
			</Box>

			<Dialog
				open={open}
				onClose={() => setOpen(false)}
				fullScreen={isMobile}
				maxWidth='md'
				fullWidth
			>
				<DialogTitle textAlign='center'>Создание нового рекламного заказа</DialogTitle>

				<DialogContent
					dividers
					sx={{ padding: 1 }}
				>
					<div className='grid grid-cols-1 md:grid-cols-1 gap-2 p-0'>
						<TextField
							label='Название'
							fullWidth
							multiline
							rows={3}
							margin='normal'
							value={formData.name}
							onChange={handleTextChange('name')}
							slotProps={{
								htmlInput: {
									maxLength: 250,
								},
								formHelperText: {
									sx: { textAlign: 'right' },
								},
							}}
							helperText={`${formData.name.length}/250`}
						/>

						<TextField
							label='Описание'
							fullWidth
							multiline
							rows={3}
							margin='normal'
							value={formData.description}
							onChange={handleTextChange('description')}
							slotProps={{
								htmlInput: {
									maxLength: 250,
								},
								formHelperText: {
									sx: { textAlign: 'right' },
								},
							}}
							helperText={`${formData.description.length}/250`}
						/>

						<Autocomplete
							options={
								Object.values(AdOrderType).filter((v) => typeof v === 'number') as AdOrderType[]
							}
							getOptionLabel={(option) =>
								ORDER_TYPE_AD_CONFIG[option as AdOrderType]?.label || 'Unknown'
							}
							value={formData.broadcast_type}
							onChange={(_, newValue) => {
								setFormData((prev) => ({
									...prev,
									broadcast_type: newValue as AdOrderType,
								}))
							}}
							renderInput={(params) => (
								<TextField
									{...params}
									label='Тип вещания'
									margin='normal'
								/>
							)}
							renderOption={(props, option) => {
								const config = ORDER_TYPE_AD_CONFIG[option as AdOrderType]
								const { key, ...restProps } = props
								return (
									<li
										key={key}
										{...restProps}
									>
										<Box
											display='flex'
											gap={2}
											alignItems='center'
											width='100%'
											sx={{
												'&:hover': {
													backgroundColor: 'rgba(141,202,246,0.3)',
													cursor: 'pointer',
												},
												padding: '8px 16px',
											}}
										>
											<config.icon fontSize='small' />
											<span>{config.label}</span>
										</Box>
									</li>
								)
							}}
						/>
						<ParametersBlock
							type={formData.broadcast_type}
							parameters={formData.parameters}
							onChange={(params) => setFormData((prev) => ({ ...prev, parameters: params }))}
						/>

						<Box
							display={'flex'}
							justifyContent={'center'}
							alignItems={'center'}
							gap={2}
						>
							<DateTimePicker
								label='Начальная дата'
								value={dayjs(formData.broadcast_interval.lower)}
								onChange={handleDateChange('lower')}
								format='DD.MM.YYYY HH:mm'
								slotProps={{
									textField: {
										fullWidth: true,
										margin: 'normal',
										error: !formData.broadcast_interval.lower,
										helperText: !formData.broadcast_interval.lower
											? 'Обязательное поле'
											: 'Формат: ДД.ММ.ГГГГ ЧЧ:мм',
									},
								}}
							/>

							<DateTimePicker
								label='Конечная дата'
								value={dayjs(formData.broadcast_interval.upper)}
								onChange={handleDateChange('upper')}
								format='DD.MM.YYYY HH:mm'
								slotProps={{
									textField: {
										fullWidth: true,
										margin: 'normal',
										error: !formData.broadcast_interval.upper,
										helperText: !formData.broadcast_interval.upper
											? 'Обязательное поле'
											: 'Формат: ДД.ММ.ГГГГ ЧЧ:мм',
									},
								}}
							/>
						</Box>
						<Autocomplete
							multiple
							options={clients}
							getOptionLabel={(option) => option.name}
							filterOptions={(x) => x}
							value={formData.clients}
							onChange={(_, newValue) => {
								setFormData((prev) => ({
									...prev,
									clients: newValue,
								}))
							}}
							onInputChange={(_, value) => {
								requestAnimationFrame(() => {
									setClientsSearch(value)
								})
							}}
							isOptionEqualToValue={(option, value) => option.id === value.id}
							loading={isLoadingClients}
							slotProps={{
								listbox: {
									onScroll: handleClientsScroll,
									style: { maxHeight: 300, overflow: 'auto' },
								},
							}}
							renderInput={(params) => (
								<TextField
									{...params}
									label='Клиенты'
									margin='normal'
									helperText='Начните вводить для поиска клиентов'
									slotProps={{
										root: {
											// Для кастомизации корневого элемента TextField
										},
										htmlInput: {
											...params.inputProps,
											endadornment: (
												<>
													{isLoadingClients && (
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
										key={option.id}
										label={option.name}
									/>
								))
							}
							renderOption={(props, option, { selected }) => {
								const { key, ...restProps } = props
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
													backgroundColor: 'rgba(141,202,246,0.3)',
													cursor: 'pointer',
												},
												padding: '8px 16px',
											}}
										>
											<Typography>{option.name}</Typography>
											<Checkbox checked={selected} />
										</Box>
									</li>
								)
							}}
							noOptionsText={isLoadingClients ? 'Загрузка...' : 'Ничего не найдено'}
						/>
						<Autocomplete
							multiple
							options={playlists}
							getOptionLabel={(option) => option.name}
							filterOptions={(x) => x}
							value={formData.playlist}
							onChange={(_, newValue) => {
								setFormData((prev) => ({
									...prev,
									playlist: newValue,
								}))
							}}
							onInputChange={(_, value) => {
								requestAnimationFrame(() => {
									setPlaylistsSearch(value)
								})
							}}
							isOptionEqualToValue={(option, value) => option.id === value.id}
							loading={isLoadingPlaylists}
							slotProps={{
								listbox: {
									onScroll: handlePlaylistsScroll,
									style: { maxHeight: 300, overflow: 'auto' },
								},
							}}
							renderInput={(params) => (
								<TextField
									{...params}
									label='Плейлисты'
									margin='normal'
									helperText='Начните вводить для поиска плейлистов'
									slotProps={{
										root: {
											// Для кастомизации корневого элемента TextField
										},
										htmlInput: {
											...params.inputProps,
											endadornment: (
												<>
													{isLoadingPlaylists && (
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
										key={option.id}
										label={option.name}
									/>
								))
							}
							renderOption={(props, option, { selected }) => {
								const { key, ...restProps } = props
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
													backgroundColor: 'rgba(141,202,246,0.3)',
													cursor: 'pointer',
												},
												padding: '8px 16px',
											}}
										>
											<Typography>{option.name}</Typography>
											<Checkbox checked={selected} />
										</Box>
									</li>
								)
							}}
							noOptionsText={isLoadingPlaylists ? 'Загрузка...' : 'Ничего не найдено'}
						/>
					</div>
				</DialogContent>

				<DialogActions>
					<Button onClick={() => setOpen(false)}>Отмена</Button>
					<Button
						variant='contained'
						onClick={handleSubmit}
						disabled={!formData.name}
					>
						Создать
					</Button>
				</DialogActions>
			</Dialog>
		</>
	)
}

export default CreateAdOrderModal
