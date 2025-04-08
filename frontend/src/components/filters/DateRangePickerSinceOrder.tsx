'use client'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import dayjs, { Dayjs } from 'dayjs'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { handleQueryParamChange } from '@/utils'
import { Label } from '../data-display/Label'

const DATE_FORMAT = 'YYYY-MM-DD'
const DISPLAY_FORMAT = 'DD-MM-YYYY'

const DateRangePickerSinceOrder = () => {
	const searchParams = useSearchParams()
	const pathname = usePathname()
	const router = useRouter()

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

	const handleDateChange = (type: 'since_after' | 'since_before', date: Dayjs | null) => {
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
		<div className='flex flex-row w-full justify-end items-center gap-2'>
			<Label className='text-xl text-nowrap'>Начало Эфира</Label>
			<div className='w-full flex flex-row flex-nowrap gap-1'>
				<DatePicker
					label='От'
					value={sinceAfter}
					onChange={(date) => handleDateChange('since_after', date)}
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
					value={sinceBefore}
					onChange={(date) => handleDateChange('since_before', date)}
					format={DISPLAY_FORMAT}
					slotProps={{
						textField: {
							error: errors.created_before,
							helperText: errors.created_before ? 'Некорректная дата' : '',
						},
					}}
				/>
			</div>
		</div>
	)
}

export default DateRangePickerSinceOrder
