import { createNomenclature } from '@/app/nomenclatures/api'
import { useNotification } from '@/hooks/useNotification'
import { ICreateNomenclature } from '@/types/nomeclaturesType'
import { useRouter } from 'next/navigation'
import { ChangeEvent, useState } from 'react'
import { DAY_KEYS } from '../constans/constants'

// Валидационные функции вынесены за пределы хука для переиспользования
const isValidWorktime = (value: string): boolean => {
	const regex = /^([01]\d|2[0-3]):[0-5]\d-([01]\d|2[0-3]):[0-5]\d$/
	return regex.test(value)
}

const isValidVolume = (arr: number[]): boolean => {
	return arr.length === 4 && arr.every((v) => !isNaN(v) && v >= 0 && v <= 100)
}
const defaultDaySettings: ICreateNomenclature['settings'][keyof ICreateNomenclature['settings']] = {
	worktime: '',
	default_volume: [0, 0, 0, 0],
}

const defaultSettings: ICreateNomenclature['settings'] = Object.fromEntries(
	DAY_KEYS.map((day: any) => [day, { ...defaultDaySettings }]),
) as ICreateNomenclature['settings']

export const useNomenclatureForm = () => {
	const [formState, setFormState] = useState<ICreateNomenclature>({
		name: '',
		description: '',
		version: '',
		settings: defaultSettings,
	})

	const [formErrors, setFormErrors] = useState<Record<string, string>>({})
	const [expandedDay, setExpandedDay] = useState<string | false>(false)
	const router = useRouter()
	const { showNotification } = useNotification()

	const handleTextChange =
		(field: keyof Omit<ICreateNomenclature, 'settings'>) => (e: ChangeEvent<HTMLInputElement>) => {
			const value = e.target.value.slice(0, 250)
			setFormState((prev) => ({ ...prev, [field]: value }))
		}

	const handleDaySettingChange =
		(
			day: keyof ICreateNomenclature['settings'],
			key: keyof ICreateNomenclature['settings'][(typeof DAY_KEYS)[number]],
			isDaySettings: boolean,
		) =>
		(e: ChangeEvent<HTMLInputElement>) => {
			const value = e.target.value

			setFormState((prev) => {
				const newSettings = { ...prev.settings }

				if (key === 'worktime') {
					const digits = value.replace(/\D/g, '').slice(0, 8)
					const formattedValue = formatWorktimeString(digits)

					if (isDaySettings) {
						newSettings[day] = {
							...newSettings[day],
							worktime: formattedValue,
						}
					} else {
						// Применяем настройки ко всем дням
						DAY_KEYS.forEach((dayKey) => {
							newSettings[dayKey] = {
								...newSettings[dayKey],
								worktime: formattedValue,
							}
						})
					}
				}

				if (key === 'default_volume') {
					const parsedValue = parseVolumeString(value)

					if (isDaySettings) {
						newSettings[day] = {
							...newSettings[day],
							default_volume: parsedValue,
						}
					} else {
						// Применяем настройки ко всем дням
						DAY_KEYS.forEach((dayKey) => {
							newSettings[dayKey] = {
								...newSettings[dayKey],
								default_volume: parsedValue,
							}
						})
					}
				}

				return { ...prev, settings: newSettings }
			})
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

	const parseVolumeString = (value: string): [number, number, number, number] => {
		const values = value
			.replace(/\s/g, '')
			.split(',')
			.map((v) => parseInt(v, 10))
			.filter((v) => !isNaN(v) && v >= 0 && v <= 100)
			.slice(0, 4)

		while (values.length < 4) {
			values.push(0)
		}

		return values as [number, number, number, number]
	}

	const validateForm = (): boolean => {
		const errors: Record<string, string> = {}

		DAY_KEYS.forEach((day) => {
			const { worktime, default_volume } = formState.settings[day]

			if (!isValidWorktime(worktime)) {
				errors[`${day}-worktime`] = 'Неверный формат (должен быть HH:MM-HH:MM)'
			}

			if (!isValidVolume(default_volume)) {
				errors[`${day}-volume`] = 'Введите 4 числа от 0 до 100 через запятую'
			}
		})

		setFormErrors(errors)
		return Object.keys(errors).length === 0
	}

	const handleSubmit = async (onSuccess?: () => void) => {
		if (!validateForm()) return

		try {
			await createNomenclature(formState)
			resetForm()
			router.refresh()
			showNotification(`Номенклатура успешно создана`, 'success')
			onSuccess?.()
		} catch (error) {
			console.error('Ошибка создания:', error)
			showNotification(
				`Ошибка создания: ${error instanceof Error ? error.message : String(error)}`,
				'error',
			)
		}
	}

	const handleCopyMondaySettings = () => {
		const mondaySettings = formState.settings.mon
		const newSettings = { ...formState.settings }

		DAY_KEYS.forEach((day) => {
			if (day === 'mon') return
			newSettings[day] = {
				worktime: mondaySettings.worktime,
				default_volume: [...mondaySettings.default_volume],
			}
		})

		setFormState((prev) => ({ ...prev, settings: newSettings }))
		showNotification('Настройки с понедельника скопированы на остальные дни', 'info')
	}

	const resetForm = () => {
		setFormState({
			name: '',
			description: '',
			version: '',
			settings: defaultSettings,
		})
		setFormErrors({})
		setExpandedDay(false)
	}

	const handleVolumeChange = (
		day: keyof ICreateNomenclature['settings'],
		newVolume: number[],
		isDaySettings: boolean,
	) => {
		setFormState((prev) => {
			const newSettings = { ...prev.settings }

			if (isDaySettings) {
				newSettings[day] = {
					...newSettings[day],
					default_volume: newVolume.slice(0, 4) as [number, number, number, number],
				}
			} else {
				// Применяем настройки ко всем дням
				DAY_KEYS.forEach((dayKey) => {
					newSettings[dayKey] = {
						...newSettings[dayKey],
						default_volume: newVolume.slice(0, 4) as [number, number, number, number],
					}
				})
			}

			return { ...prev, settings: newSettings }
		})
	}

	return {
		formState,
		formErrors,
		expandedDay,
		handleTextChange,
		handleDaySettingChange,
		handleSubmit,
		handleCopyMondaySettings,
		setExpandedDay,
		resetForm,
		handleVolumeChange,
	}
}
