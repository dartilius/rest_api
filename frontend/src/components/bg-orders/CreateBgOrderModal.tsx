'use client'

import { getClients } from '@/app/adorders/api'
import { getPlayLists } from '@/app/playlists/api'
import { BgOrderType, IBroadcastInterval, ORDER_TYPE_BG_CONFIG } from '@/types/orderTypes'
import { IPlayList } from '@/types/playListsTypes'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import {
	Autocomplete,
	Box,
	Button,
	Dialog,
	DialogActions,
	DialogContent,
	DialogTitle,
	TextField,
	useMediaQuery,
	useTheme,
} from '@mui/material'
import { DateTimePicker } from '@mui/x-date-pickers'
import dayjs, { Dayjs } from 'dayjs'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import ActionButton from '../Ui/button/ActionButton'

import AsyncAutocomplete from '../Ui/AsyncAutocomplete'
import { useNotification } from '@/hooks/useNotification'
import ParametersBlockBg from './ParametersBlockBg'
import { BgOrderPayload, createBgOrder } from '@/app/bgorders/api'

interface Client {
	id: string
	name: string
}

export interface FormStateBg {
	name: string
	description: string
	order_type: BgOrderType
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

const CreateBgOrderModal = () => {
	const router = useRouter()
	const theme = useTheme()
	const { showNotification } = useNotification()
	const [open, setOpen] = useState<boolean>(false)
	const [formData, setFormData] = useState<FormStateBg>({
		name: '',
		description: '',
		order_type: BgOrderType.MUSIC,
		parameters: {
			weight: 50,
			times_in_hour: 1,
		},
		playlist: [],
		clients: [],
		broadcast_interval: { lower: '', upper: '' },
	})

	const isMobile = useMediaQuery(theme.breakpoints.down('sm'))

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
			const payload: BgOrderPayload = [
				{
					...formData,
					clients: formData.clients.map((c) => c.id),
					playlist: formData.playlist.map((p) => p.id).toString(),
					broadcast_interval: {
						lower: formData.broadcast_interval.lower,
						upper: formData.broadcast_interval.upper,
					},
				},
			]
			const resp = await createBgOrder(payload)
			console.log(resp)
			showNotification('Заказ успешно создан', 'success')
			setOpen(false)
			router.refresh()
		} catch (error) {
			console.error('Ошибка создания заказа:', error)
			showNotification('Ошибка создания заказа', 'error')
		}
	}

	const handleTextChange =
		(field: keyof FormStateBg) => (e: React.ChangeEvent<HTMLInputElement>) => {
			const value = e.target.value.slice(0, 250)
			setFormData((prev) => ({ ...prev, [field]: value }))
		}

	return (
		<>
					<Box
				display='flex'
				width='20%'
				height={'100%'}
				justifyContent='center'
				alignItems='center'
			>
				{isMobile ? (
					<ActionButton
						variant='primary'
						size='sm'
						icon={AddCircleOutlineIcon}
						onClick={() => setOpen(true)}
						className='h-full m-2'
					/>
				) : (
					<ActionButton
						variant='primary'
						size='lg'
						icon={AddCircleOutlineIcon}
						onClick={() => setOpen(true)}
					>
						Создать
					</ActionButton>
				)}
			</Box>

			<Dialog
				open={open}
				onClose={() => setOpen(false)}
				fullScreen={isMobile}
				maxWidth='md'
				fullWidth
			>
				<DialogTitle textAlign='center'>Создание фонового заказа</DialogTitle>
				<DialogContent
					dividers
					sx={{ padding: 1 }}
				>
					<div className='grid grid-cols-1 md:grid-cols-1 gap-2 p-0'>
						<TextField
							label='Название'
							fullWidth
							margin='normal'
							value={formData.name}
							onChange={handleTextChange('name')}
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
							helperText={`${formData.description.length}/250`}
						/>

						<Autocomplete
							options={
								Object.values(BgOrderType).filter((v) => typeof v === 'number') as BgOrderType[]
							}
							getOptionLabel={(option: BgOrderType) =>
								ORDER_TYPE_BG_CONFIG[option as BgOrderType]?.label || 'Unknown'
							}
							value={formData.order_type}
							onChange={(_, newValue) => {
								setFormData((prev) => ({
									...prev,
									broadcast_type: newValue as BgOrderType,
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
								const config = ORDER_TYPE_BG_CONFIG[option as BgOrderType]
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
						<ParametersBlockBg
							type={formData.order_type}
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
						<AsyncAutocomplete<Client>
							loadOptions={getClients}
							value={formData.clients}
							onChange={(newValue) => setFormData((prev) => ({ ...prev, clients: newValue }))}
							label='Клиенты'
							multiple
							getOptionLabel={(option) => option.name || ''}
							isOptionEqualToValue={(option, value) => option.id === value.id}
							helperText='Начните вводить для поиска клиентов'
						/>

						<AsyncAutocomplete<IPlayList>
							loadOptions={getPlayLists}
							value={formData.playlist}
							onChange={(newValue) => setFormData((prev) => ({ ...prev, playlist: newValue }))}
							label='Плейлисты'
							getOptionLabel={(option) => option.name || ''}
							isOptionEqualToValue={(option, value) => option.id === value.id}
							helperText='Начните вводить для поиска плейлистов'
						/>
					</div>
				</DialogContent>
				<DialogActions>
					<Button onClick={() => setOpen(false)}>Отмена</Button>
					<Button
						variant='contained'
						onClick={handleSubmit}
					>
						Создать
					</Button>
				</DialogActions>
			</Dialog>
		</>
	)
}

export default CreateBgOrderModal
