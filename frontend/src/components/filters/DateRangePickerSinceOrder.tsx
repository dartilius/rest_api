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

const DateRangePickerSinceOrder = () => {
	const searchParams = useSearchParams()
	const pathname = usePathname()
	const router = useRouter()
	const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down('md'))
	const [sinceAfter, setSinceAfter] = useState<Dayjs | null>(null)
	const [sinceBefore, setSinceBefore] = useState<Dayjs | null>(null)
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

		setSinceAfter(parseDate(searchParams?.get('since_after')))
		setSinceBefore(parseDate(searchParams?.get('since_before')))
	}, [searchParams])

	const handleDateChange = (type: string, date: Dayjs | null) => {
		const isValid = isValidDate(date)
		setErrors((prev) => ({ ...prev, [type]: !isValid }))

		let dateString = ''
		if (isValid && date) {
			dateString = date.format(DATE_FORMAT)
		}

		// Обновление состояния только при валидных датах
		if (type === 'since_after') {
			setSinceAfter(isValid ? date : null)
		} else {
			setSinceBefore(isValid ? date : null)
		}

		handleQueryParamChange(router, pathname, searchParams, type, dateString)
	}

	return (
		<>
			{isMobile ? (
				<MobileViewDatePicker
					label='Начало Эфира'
					valueFrom={sinceAfter}
					valueTo={sinceBefore}
					typeAfter={'since_after'}
					typeBefore={'since_before'}
					onChange={handleDateChange}
					formatDate={DISPLAY_FORMAT}
					errors={errors}
				/>
			) : (
				<DesktopViewDatePicker
					label='Начало Эфира'
					valueFrom={sinceAfter}
					valueTo={sinceBefore}
					typeAfter={'since_after'}
					typeBefore={'since_before'}
					onChange={handleDateChange}
					formatDate={DISPLAY_FORMAT}
					errors={errors}
				/>
			)}
		</>
	)
}

export default DateRangePickerSinceOrder
