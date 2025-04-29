'use client'
import {
	Dialog,
	DialogActions,
	DialogContent,
	DialogTitle,
	FormControl,
	MenuItem,
	Select,
	Switch,
	TextField,
	useMediaQuery,
	useTheme,
} from '@mui/material'
import { INomenclatureResponse, IUpdateNomenclature } from '@/types/nomeclaturesType'
import { useEffect, useState } from 'react'
import { CopyButton } from '@/components/Ui/button/CoppyButton'
import { getTimezoneLabel, timezonesArray } from '@/types/timeZone'
import { Label } from '@/components/data-display/Label'
import NomenclatureVolume from '@/components/nomenclatures/NomenclatureVolume/NomenclatureVolume'
import { DaySettingsGrid } from '../CreateNomenclature/components/DaySettings'
import { DAY_KEYS } from '../CreateNomenclature/constans/constants'
import { DaySettingsAccordion } from '../CreateNomenclature/components'
import { useNotification } from '@/hooks/useNotification'
import ActionButton from '@/components/Ui/button/ActionButton'
import { updateNomenclature } from '../../api'

interface TestProps {
	id: string
	openModal: boolean
	onClose: () => void
	data: INomenclatureResponse
}
const formatWorktimeString = (digits: string): string => {
	let formatted = ''

	if (digits.length >= 4) {
		formatted = `${digits.slice(0, 2)}:${digits.slice(2, 4)}`
	} else if (digits.length >= 2) {
		formatted = `${digits.slice(0, 2)}:${digits.slice(2)}`
	} else {
		formatted = digits
	}

	if (digits.length >= 8) {
		formatted += `-${digits.slice(4, 6)}:${digits.slice(6, 8)}`
	} else if (digits.length > 4) {
		formatted += `-${digits.slice(4)}`
	}

	return formatted
}

function Test({ id, openModal, onClose, data }: TestProps) {
	const [name, setName] = useState<string>('')
	const [description, setDescription] = useState<string>('')
	const [settings, setSettings] = useState<INomenclatureResponse['settings']>({})
	const [isDaySettings, setIsDaySettings] = useState<boolean>(false)
	const [expandedDay, setExpandedDay] = useState<string | false>(false)
	const [timezone, setTimezone] = useState<string>(data.main_info.timezone)
	const [worktime, setWorktime] = useState<string>('')
	const [volume, setVolume] = useState<[number, number, number, number]>([0, 0, 0, 0])
	const [currentDay, setCurrentDay] = useState<string>('mon')
	const [dayWorktime, setDayWorktime] = useState<string>('')
	const [dayVolume, setDayVolume] = useState<[number, number, number, number]>([0, 0, 0, 0])
	const [errors, setErrors] = useState<{
		worktime?: string
		volume?: string
	}>({})
	const theme = useTheme()
	const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
	const { showNotification } = useNotification()

	useEffect(() => {
		setName(data.main_info.name)
		setDescription(data.main_info.description)
		setSettings(data.settings)
		setTimezone(data.main_info.timezone)
		setWorktime(data.settings.mon?.worktime || '')
		setVolume(data.settings.mon?.default_volume || [0, 0, 0, 0])
		setDayWorktime(data.settings.mon?.worktime || '')
		setDayVolume(data.settings.mon?.default_volume || [0, 0, 0, 0])
	}, [data])

	const handleWorktimeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		const value = e.target.value
		// Разрешаем только цифры, двоеточия и дефис
		const sanitizedValue = value.replace(/[^\d:-]/g, '')
		setWorktime(sanitizedValue)
		setErrors((prev) => ({ ...prev, worktime: undefined }))
	}

	const handleWorktimeBlur = (e: React.FocusEvent<HTMLInputElement>) => {
		const value = e.target.value
		if (!value) {
			setWorktime('')
			return
		}
		// Проверяем формат и форматируем если нужно
		const parts = value.split('-')
		if (parts.length === 2) {
			const [start, end] = parts
			const formattedStart = start.replace(/\D/g, '').padStart(4, '0')
			const formattedEnd = end.replace(/\D/g, '').padStart(4, '0')
			if (formattedStart.length === 4 && formattedEnd.length === 4) {
				const formattedValue = `${formattedStart.slice(0, 2)}:${formattedStart.slice(2)}-${formattedEnd.slice(0, 2)}:${formattedEnd.slice(2)}`
				setWorktime(formattedValue)
				return
			}
		}
		// Если формат неверный, форматируем как обычно
		const digits = value.replace(/\D/g, '')
		const formattedValue = formatWorktimeString(digits)
		setWorktime(formattedValue)
	}

	const handleVolumeChange = (newVolume: [number, number, number, number]) => {
		setVolume(newVolume)
		setErrors((prev) => ({ ...prev, volume: undefined }))
	}

	const handleDayExpand = (day: string) => () => {
		setExpandedDay(expandedDay === day ? false : day)
		setCurrentDay(day)
		setDayWorktime(settings[day]?.worktime || '')
		setDayVolume(settings[day]?.default_volume || [0, 0, 0, 0])
	}

	const handleDayWorktimeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		setDayWorktime(e.target.value)
		setErrors((prev) => ({ ...prev, worktime: undefined }))
	}

	const handleDayWorktimeBlur = (e: React.FocusEvent<HTMLInputElement>) => {
		const value = e.target.value
		if (!value) {
			setDayWorktime('')
			return
		}
		const parts = value.split('-')
		if (parts.length === 2) {
			const [start, end] = parts
			const formattedStart = start.replace(/\D/g, '').padStart(4, '0')
			const formattedEnd = end.replace(/\D/g, '').padStart(4, '0')
			if (formattedStart.length === 4 && formattedEnd.length === 4) {
				const formattedValue = `${formattedStart.slice(0, 2)}:${formattedStart.slice(2)}-${formattedEnd.slice(0, 2)}:${formattedEnd.slice(2)}`
				setDayWorktime(formattedValue)
				return
			}
		}
		const digits = value.replace(/\D/g, '')
		const formattedValue = formatWorktimeString(digits)
		setDayWorktime(formattedValue)
	}

	const handleDayVolumeChange = (newVolume: [number, number, number, number]) => {
		setDayVolume(newVolume)
		setErrors((prev) => ({ ...prev, volume: undefined }))
	}

	const handleCopyMondaySettings = () => {
		const mondaySettings = settings.mon
		const newSettings = { ...settings }

		DAY_KEYS.forEach((day) => {
			if (day === 'mon') return
			newSettings[day] = {
				worktime: mondaySettings.worktime,
				default_volume: [...mondaySettings.default_volume],
			}
		})

		setSettings(newSettings)
		showNotification('Настройки с понедельника скопированы на остальные дни', 'info')
	}

	const convertToEtcFormat = (timezone: string): string => {
		if (timezone.startsWith('UTC')) {
			const offset = timezone.replace('UTC', '').trim()
			return `Etc/GMT${offset}`
		}
		return timezone
	}

	const handleSave = async () => {
		try {
			const updatedSettings = isDaySettings
				? {
						...settings,
						[currentDay]: {
							worktime: dayWorktime,
							default_volume: dayVolume,
						},
					}
				: Object.fromEntries(
						DAY_KEYS.map((day) => [
							day,
							{
								worktime,
								default_volume: volume,
							},
						]),
					)

			const updatedNomenclature: IUpdateNomenclature = {
				name,
				description,
				timezone: convertToEtcFormat(timezone),
				settings: updatedSettings,
			}
			await updateNomenclature(data.id, updatedNomenclature)
			showNotification('Данные успешно обновлены', 'success')
		} catch (error: any) {
			showNotification('Ошибка при обновлении данных', 'error')
			console.error('Ошибка при обновлении:', error)
		}
	}

	return (
		<Dialog
			open={openModal}
			onClose={onClose}
			fullScreen={isMobile}
			maxWidth='md'
			fullWidth
		>
			<DialogTitle className='text-center bg-gradient-to-r from-cyan-600 to-blue-500 shadow text-white'>
				<div className='text-2xl font-bold'>Изменить номенклатуру</div>
			</DialogTitle>
			<DialogContent
				dividers
				className='bg-gradient-to-r from-cyan-600 to-blue-500 shadow  p-4 md:p-6 gap-3 flex flex-col'
			>
				<Label className='text-xl'>Название</Label>
				<input
					value={name}
					className='w-full font-bold text-2xl text-amber-300 drop-shadow-[0_1px_2px_rgba(0,0,0,0.4)] bg-inherit border-2 border-gray-300 rounded-lg p-4'
					onChange={(e) => setName(e.target.value)}
				/>
				<Label className='text-xl'>Описание</Label>
				<input
					value={description}
					className='text-pink-100 bg-inherit font-semibold text-xl border-2 border-gray-300 rounded-lg p-1 w-full'
					onChange={(e) => setDescription(e.target.value)}
				/>
				<Label className='text-xl'>Часовой пояс</Label>
				<FormControl
					fullWidth
					className='text-base text-violet-200 w-full'
				>
					<Select
						value={timezone}
						defaultValue={timezone}
						onChange={(event) => setTimezone(event.target.value as string)}
						style={{
							borderRadius: '4px',
							maxHeight: '36px',
							border: 'none',
							fontSize: '1.4rem',
							lineHeight: '1.9rem',
							color: 'rgb(221 214 254 / var(--tw-text-opacity, 1))',
						}}
						displayEmpty
						renderValue={(value) => {
							return getTimezoneLabel(value)
						}}
					>
						{timezonesArray.map((item, key) => (
							<MenuItem
								key={key}
								value={item.value}
							>
								{item.label}
							</MenuItem>
						))}
					</Select>
				</FormControl>
				<Label className='text-xl'>Настройки</Label>
				<div className='flex flex-col gap-4 items-center'>
					<div className='flex items-center gap-1'>
						<span>Общая настройка</span>
						<Switch
							checked={isDaySettings}
							onChange={() => setIsDaySettings(!isDaySettings)}
							color='secondary'
						/>

						<span>Настройка для каждого дня</span>
					</div>
					{!isDaySettings ? (
						<div className='flex flex-col gap-1 items-center'>
							<TextField
								label='Рабочее время'
								fullWidth
								margin='dense'
								value={worktime}
								onChange={handleWorktimeChange}
								onBlur={handleWorktimeBlur}
								error={!!errors.worktime}
								helperText={
									errors.worktime ||
									'Введите время в формате hh:mm-hh:mm или просто цифры (например: 10002100)'
								}
								placeholder='Например: 10002100 или 10:00-21:00'
							/>
							<NomenclatureVolume
								value={volume}
								onChange={handleVolumeChange}
								error={!!errors.volume}
								helperText={errors.volume}
							/>
						</div>
					) : (
						<div className='flex flex-col gap-4 items-center'>
							<CopyButton
								onCopy={handleCopyMondaySettings}
								label='Применить настройки для всех дней'
								disabled={!worktime || volume.some((v) => v === 0)}
							/>
							<DaySettingsGrid>
								{DAY_KEYS.map((day) => (
									<DaySettingsAccordion
										key={day}
										day={day}
										expanded={expandedDay === day}
										onExpandChange={handleDayExpand(day)}
										settings={{
											worktime: day === currentDay ? dayWorktime : settings[day]?.worktime || '',
											default_volume:
												day === currentDay
													? dayVolume
													: settings[day]?.default_volume || [0, 0, 0, 0],
										}}
										errors={errors}
										onWorktimeChange={handleDayWorktimeChange}
										onVolumeChange={handleDayVolumeChange}
										handleWorktimeBlur={handleDayWorktimeBlur}
									/>
								))}
							</DaySettingsGrid>
						</div>
					)}
				</div>
			</DialogContent>
			<DialogActions className='bg-gradient-to-r from-cyan-600 to-blue-500 shadow  p-4 md:p-6 gap-3 flex flex-col'>
				<div className='flex w-full justify-end flex-row mt-4'>
					<ActionButton
						onClick={handleSave}
						className='w-48 flex justify-center items-center'
						variant='secondary'
					>
						Сохранить
					</ActionButton>
				</div>
			</DialogActions>
		</Dialog>
	)
}

export default Test
