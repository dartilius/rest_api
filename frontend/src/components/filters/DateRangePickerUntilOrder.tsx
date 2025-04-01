'use client'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import dayjs, { Dayjs } from 'dayjs'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { handleQueryParamChange } from '@/utils'
import { Label } from '../data-display/Label'

const DATE_FORMAT = 'YYYY-MM-DD'
const DISPLAY_FORMAT = 'DD-MM-YYYY'

const DateRangePickerUntilOrder = () => {
	const searchParams = useSearchParams()
	const pathname = usePathname()
	const router = useRouter()

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

	const handleDateChange = (type: 'until_after' | 'until_before', date: Dayjs | null) => {
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

	return (
		<div className='flex flex-row w-full justify-end items-center gap-2'>
			<Label className='text-xl text-nowrap'>Окончание Эфира</Label>
			<div className='w-full flex flex-row flex-nowrap gap-1'>
			<DatePicker
				label='От'
				value={untilAfter}
				onChange={(date) => handleDateChange('until_after', date)}
				format={DISPLAY_FORMAT}
				slotProps={{
					textField: {
						error: errors.created_after,
						helperText: errors.created_after ? 'Некорректная дата' : '',
					},
				}}
			/>
			<DatePicker
				label='До'
				value={untilBefore}
				onChange={(date) => handleDateChange('until_before', date)}
				format={DISPLAY_FORMAT}
				slotProps={{
					textField: {
						error: errors.created_before,
						helperText: errors.created_before ? 'Некорректная дата' : '',
					},
				}}
			/></div>
		</div>
	)
}

export default DateRangePickerUntilOrder
