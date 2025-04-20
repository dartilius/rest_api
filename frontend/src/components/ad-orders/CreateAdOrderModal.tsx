'use client'

import {ChangeEvent, useState} from 'react'
import { client } from '@/services/httpClient'
import {
	Button,
	Dialog,
	DialogActions,
	DialogContent,
	DialogTitle,
	TextField,
	MenuItem,
	useMediaQuery,
	useTheme,
	Box,
	Typography,
} from '@mui/material'
import { DateTimePicker } from '@mui/x-date-pickers'
import { useRouter } from 'next/navigation'
import ActionButton from '../Ui/button/ActionButton'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import dayjs, { Dayjs } from 'dayjs'
import { AdOrderType, IBroadcastInterval, ORDER_TYPE_AD_CONFIG } from '@/types/orderTypes'

interface FormState {
	name: string
	description: string
	broadcastType: AdOrderType
	parameters: string
	playlist: string
	owner: string
	broadcastIntervals: IBroadcastInterval
}
const CreateAdOrderModal = () => {
	const [open, setOpen] = useState(false)
	const [formData, setFormData] = useState<FormState>({
		name: '',
		description: '',
		broadcastType: AdOrderType.POINT_TIME,
		parameters: '',
		playlist: '',
		owner: '',
		broadcastIntervals: { lower: '', upper: '' },
	})
	const router = useRouter()
	const theme = useTheme()
	const isMobile = useMediaQuery(theme.breakpoints.down('sm'))

	const handleDateChange = (field: keyof IBroadcastInterval) => (value: Dayjs | null) => {
		setFormData((prev) => ({
			...prev,
			broadcastIntervals: {
				...prev.broadcastIntervals,
				[field]: value?.toISOString() || '',
			},
		}))
	}

	const handleSubmit = async () => {
		try {
			const payload = {
				...formData,
				broadcastIntervals: {
					lower: formData.broadcastIntervals.lower,
					upper: formData.broadcastIntervals.upper,
				},
			}

			await client.post('/api/adorders', { body: payload })
			setOpen(false)
			router.refresh()
		} catch (error) {
			console.error('Ошибка создания:', error)
		}
	}

	// Общий обработчик для полей с ограничением
	const handleTextChange = (field: keyof FormState) => (e: ChangeEvent<HTMLInputElement>) => {
		const value = e.target.value.slice(0, 250)
		setFormData((prev) => ({ ...prev, [field]: value }))
	}

	return (
		<>
			<Box
				display={'flex'}
				width={'20%'}
				justifyContent={'center'}
				alignItems={'center'}
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
				<DialogTitle>Создание нового рекламного заказа</DialogTitle>

				<DialogContent dividers>
					<div className='grid grid-cols-1 md:grid-cols-1 gap-4'>
						<div>
							<TextField
								label='Название'
								type='text'
								multiline
								fullWidth
								rows={3}
								margin='normal'
								value={formData.name}
								onChange={handleTextChange('name')}
								slotProps={{
									htmlInput: {
										maxLength: 250,
									},
								}}
							/>
							<Typography
								variant='caption'
								color='textSecondary'
								sx={{ display: 'block', textAlign: 'right', mt: -1 }}
							>
								{formData.name.length}/250
							</Typography>
						</div>

						<div>
							<TextField
								label='Описание'
								fullWidth
								margin='normal'
								multiline
								rows={3}
								value={formData.description}
								onChange={handleTextChange('description')}
								slotProps={{
									htmlInput: {
										maxLength: 250,
									},
								}}
							/>
							<Typography
								variant='caption'
								color='textSecondary'
								sx={{ display: 'block', textAlign: 'right', mt: -1 }}
							>
								{formData.description.length}/250
							</Typography>
						</div>

						<TextField
							select
							label='Тип вещания'
							fullWidth
							margin='normal'
							value={formData.broadcastType}
							onChange={(e) =>
								setFormData({
									...formData,
									broadcastType: Number(e.target.value) as AdOrderType,
								})
							}
						>
							{Object.entries(ORDER_TYPE_AD_CONFIG).map(([key, config]) => {
								const typeKey = Number(key.replace('AdOrderType.', '')) as AdOrderType
								return (
									<MenuItem
										key={key}
										value={typeKey}
									>
										<Box
											display='flex'
											alignItems='center'
											gap={1}
										>
											<config.icon fontSize='small' />
											<span>{config.label}</span>
										</Box>
									</MenuItem>
								)
							})}
						</TextField>

						<DateTimePicker
							label='Начальная дата'
							value={
								formData.broadcastIntervals.lower ? dayjs(formData.broadcastIntervals.lower) : null
							}
							onChange={handleDateChange('lower')}
							slotProps={{
								textField: {
									fullWidth: true,
									margin: 'normal',
									error: !formData.broadcastIntervals.lower,
									helperText: !formData.broadcastIntervals.lower ? 'Обязательное поле' : '',
								},
							}}
						/>

						<DateTimePicker
							label='Конечная дата'
							value={
								formData.broadcastIntervals.upper ? dayjs(formData.broadcastIntervals.upper) : null
							}
							onChange={handleDateChange('upper')}
							slotProps={{
								textField: {
									fullWidth: true,
									margin: 'normal',
									error: !formData.broadcastIntervals.upper,
									helperText: !formData.broadcastIntervals.upper ? 'Обязательное поле' : '',
								},
							}}
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
