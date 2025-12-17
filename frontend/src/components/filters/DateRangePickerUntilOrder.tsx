'use client'
import dayjs, { Dayjs } from 'dayjs'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { handleQueryParamChange } from '@/utils'
import { Theme, useMediaQuery } from '@mui/material'
import MobileViewDatePicker from '../Ui/datePicker/MobileViewDatePicker'
import DesktopViewDatePicker from '../Ui/datePicker/DesktopViewDatePicker'

const DATE_FORMAT = 'YYYY-MM-DD'
const DISPLAY_FORMAT = 'DD-MM-YYYY'

const DateRangePickerUntilOrder = () => {
	const searchParams = useSearchParams()
	const pathname = usePathname()
	const router = useRouter()
	const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down('md'))
	const [untilAfter, setUntilAfter] = useState<Dayjs | null>(null)
	const [untilBefore, setUntilBefore] = useState<Dayjs | null>(null)
	const [errors, setErrors] = useState<Record<string, boolean>>({
		since: false,
		until: false,
	})

	// Валидация даты
	const isValidDate = (date: Dayjs | null): boolean => {
		return date ? date.isValid() : false
	}

	useEffect(() => {
		const parseDate = (dateString: string | null) => {
			if (!dateString) return null
			const date = dayjs(dateString, DATE_FORMAT, true) // strict parsing
			return date.isValid() ? date : null
		}

		setUntilAfter(parseDate(searchParams?.get('until_after')))
		setUntilBefore(parseDate(searchParams?.get('until_before')))
	}, [searchParams])

	const handleDateChange = (type: string, date: Dayjs | null) => {
		const isValid = isValidDate(date)
		setErrors((prev) => ({ ...prev, [type]: !isValid }))

		let dateString = ''
		if (isValid && date) {
			dateString = date.format(DATE_FORMAT)
		}

		// Обновление состояния только при валидных датах
		if (type === 'until_after') {
			setUntilAfter(isValid ? date : null)
		} else {
			setUntilBefore(isValid ? date : null)
		}

		handleQueryParamChange(router, pathname, searchParams, type, dateString)
	}
	// Мобильная версия

	return (
		<>
			{isMobile ? (
				<MobileViewDatePicker
					label='Окончание Эфира'
					valueFrom={untilAfter}
					valueTo={untilBefore}
					typeAfter={'until_after'}
					typeBefore={'until_before'}
					onChange={handleDateChange}
					formatDate={DISPLAY_FORMAT}
					errors={errors}
				/>
			) : (
				<DesktopViewDatePicker
					label='Окончание Эфира'
					valueFrom={untilAfter}
					valueTo={untilBefore}
					typeAfter={'until_after'}
					typeBefore={'until_before'}
					onChange={handleDateChange}
					formatDate={DISPLAY_FORMAT}
					errors={errors}
				/>
			)}
		</>
	)
}

export default DateRangePickerUntilOrder
