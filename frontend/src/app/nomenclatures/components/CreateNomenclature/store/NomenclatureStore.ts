import { DAY_KEYS } from '@/app/nomenclatures/components/CreateNomenclature/constans/constants'
import { createNomenclature } from '@/services/NomenclaturesService'
import { makeAutoObservable } from 'mobx'
import { ICreateNomenclature } from '@/types/nomeclaturesType'
import { ChangeEvent } from 'react'

class NomenclatureStore {
	formState: ICreateNomenclature = {
		name: '',
		description: '',
		version: '',
		settings: Object.fromEntries(
			DAY_KEYS.map((day) => [day, { worktime: '', default_volume: [0, 0, 0, 0] }]),
		),
	}

	formErrors: Record<string, string> = {}
	expandedDay: string | false = false

	constructor() {
		makeAutoObservable(this)
	}

	// Обработчик изменения текста
	handleTextChange =
		(field: keyof Omit<ICreateNomenclature, 'settings'>) => (e: ChangeEvent<HTMLInputElement>) => {
			this.formState = {
				...this.formState,
				[field]: e.target.value, // Используем e.target.value для обновления поля
			}
		}

	// Обработчик изменения настроек для дня
	handleDaySettingChange =
		(
			day: keyof ICreateNomenclature['settings'],
			key: keyof ICreateNomenclature['settings'][keyof ICreateNomenclature['settings']],
		) =>
		(value: string) => {
			const newSettings = { ...this.formState.settings }

			if (key === 'worktime') {
				const digits = value.replace(/\D/g, '').slice(0, 8)
				newSettings[day] = {
					...newSettings[day],
					worktime: this.formatWorktimeString(digits),
				}
			}

			if (key === 'default_volume') {
				newSettings[day] = {
					...newSettings[day],
					default_volume: this.parseVolumeString(value),
				}
			}

			this.formState = { ...this.formState, settings: newSettings }
		}

	// Форматирование времени работы
	formatWorktimeString = (digits: string): string => {
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

	// Разбор строковых значений для объема
	parseVolumeString = (value: string): [number, number, number, number] => {
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

	// Валидация формы
	validateForm = (): boolean => {
		const errors: Record<string, string> = {}

		DAY_KEYS.forEach((day) => {
			const { worktime, default_volume } = this.formState.settings[day]

			if (!this.isValidWorktime(worktime)) {
				errors[`${day}-worktime`] = 'Неверный формат (должен быть HH:MM-HH:MM)'
			}

			if (!this.isValidVolume(default_volume)) {
				errors[`${day}-volume`] = 'Введите 4 числа от 0 до 100 через запятую'
			}
		})

		this.formErrors = errors
		return Object.keys(errors).length === 0
	}

	isValidWorktime = (value: string): boolean => {
		const regex = /^([01]\d|2[0-3]):[0-5]\d-([01]\d|2[0-3]):[0-5]\d$/
		return regex.test(value)
	}

	isValidVolume = (arr: number[]): boolean => {
		return arr.length === 4 && arr.every((v) => !isNaN(v) && v >= 0 && v <= 100)
	}

	// Отправка формы
	handleSubmit = async (
		showNotification: (message: string, type: 'success' | 'error' | 'info') => void,
		onSuccess?: () => void,
	) => {
		if (!this.validateForm()) return
        console.log(1)
		try {
			await createNomenclature(this.formState)
			this.resetForm()
			showNotification('Номенклатура успешно создана', 'success')
			onSuccess?.()
		} catch (error) {
			console.error('Ошибка создания:', error)
			showNotification(
				`Ошибка создания: ${error instanceof Error ? error.message : String(error)}`,
				'error',
			)
		}
	}

	// Копирование настроек понедельника
	handleCopyMondaySettings = () => {
		const mondaySettings = this.formState.settings.mon
		const newSettings = { ...this.formState.settings }

		DAY_KEYS.forEach((day) => {
			if (day === 'mon') return
			newSettings[day] = {
				worktime: mondaySettings.worktime,
				default_volume: [...mondaySettings.default_volume],
			}
		})

		this.formState = { ...this.formState, settings: newSettings }
	}


	handleVolumeChange = (day: string, newVolume: [number, number, number, number]) => {
		const newSettings = { ...this.formState.settings }
		newSettings[day] = {
			...newSettings[day],
			default_volume: newVolume,
		}
		this.formState = { ...this.formState, settings: newSettings }
	}

	// Сброс формы
	resetForm = () => {
		this.formState = {
			name: '',
			description: '',
			version: '',
			settings: Object.fromEntries(
				DAY_KEYS.map((day) => [day, { worktime: '', default_volume: [0, 0, 0, 0] }]),
			),
		}
		this.formErrors = {}
		this.expandedDay = false
	}

	setExpandedDay = (day: string | false) => {
		this.expandedDay = day
	}
}

export const nomenclatureStore = new NomenclatureStore()
