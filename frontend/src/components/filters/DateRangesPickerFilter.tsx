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

const DateRangesPickerFilter = () => {
	const searchParams = useSearchParams()
	const pathname = usePathname()
	const router = useRouter()
	const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down('md'))
	const [createdAfter, setCreatedAfter] = useState<Dayjs | null>(null)
	const [createdBefore, setCreatedBefore] = useState<Dayjs | null>(null)
	const [errors, setErrors] = useState<Record<string, boolean>>({
		created_after: false,
		created_before: false,
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

		setCreatedAfter(parseDate(searchParams?.get('created_after')))
		setCreatedBefore(parseDate(searchParams?.get('created_before')))
	}, [searchParams])

	const handleDateChange = (type: string, date: Dayjs | null) => {
		const isValid = isValidDate(date)
		setErrors((prev) => ({ ...prev, [type]: !isValid }))

		let dateString = ''
		if (isValid && date) {
			dateString = date.format(DATE_FORMAT)
		}

		// Обновление состояния только при валидных датах
		if (type === 'created_after') {
			setCreatedAfter(isValid ? date : null)
		} else {
			setCreatedBefore(isValid ? date : null)
		}

		handleQueryParamChange(router, pathname, searchParams, type, dateString)
	}

	return (
		<>
			{isMobile ? (
				<MobileViewDatePicker
					label='Дата создания'
					valueFrom={createdAfter}
					valueTo={createdBefore}
					typeAfter={'created_after'}
					typeBefore={'created_before'}
					onChange={handleDateChange}
					formatDate={DISPLAY_FORMAT}
					errors={errors}
				/>
			) : (
				<DesktopViewDatePicker label='Дата создания'
					valueFrom={createdAfter}
					valueTo={createdBefore}
					typeAfter={'created_after'}
					typeBefore={'created_before'}
					onChange={handleDateChange}
					formatDate={DISPLAY_FORMAT}
					errors={errors}/>
			)}
		</>
	)
	// 	return (
	// 		<div className='flex flex-col w-full gap-2 p-1'>
	// 			<Label className='text-sm md:text-2xl text-nowrap'>Дата создания</Label>

	// 			<div className='flex flex-col gap-2'>
	// 				<DatePicker
	// 					label='От'
	// 					value={createdAfter}
	// 					onChange={(date) => handleDateChange('created_after', date)}
	// 					format={DISPLAY_FORMAT}
	// 					slotProps={{
	// 						textField: {
	// 							size: 'small',
	// 							fullWidth: true,
	// 							error: errors.created_after,
	// 							helperText: errors.created_after ? 'Некорректная дата' : '',
	// 						},
	// 					}}
	// 				/>
	// 				<DatePicker
	// 					label='До'
	// 					value={createdBefore}
	// 					onChange={(date) => handleDateChange('created_before', date)}
	// 					format={DISPLAY_FORMAT}
	// 					slotProps={{
	// 						textField: {
	// 							size: 'small',
	// 							fullWidth: true,
	// 							error: errors.created_after,
	// 							helperText: errors.created_after ? 'Некорректная дата' : '',
	// 						},
	// 					}}
	// 				/>
	// 			</div>
	// 		</div>
	// 	)
	// }

	// Десктопная версия
	// return (
	// 	<div className='flex flex-row w-full justify-end items-center gap-2'>
	// 		<Label className='text-sm md:text-xl text-nowrap'>Дата создания</Label>
	// 		<div className='w-full flex flex-row justify-end flex-nowrap gap-1'>
	// 			<DatePicker
	// 				label='От'
	// 				value={createdAfter}
	// 				onChange={(date) => handleDateChange('created_after', date)}
	// 				format={DISPLAY_FORMAT}
	// 				slotProps={{
	// 					textField: {
	// 						size: 'small',
	// 						fullWidth: true,
	// 						error: errors.created_after,
	// 						helperText: errors.created_after ? 'Некорректная дата' : '',
	// 					},
	// 				}}
	// 			/>
	// 			<DatePicker
	// 				label='До'
	// 				value={createdBefore}
	// 				onChange={(date) => handleDateChange('created_before', date)}
	// 				format={DISPLAY_FORMAT}
	// 				slotProps={{
	// 					textField: {
	// 						size: 'small',
	// 						fullWidth: true,
	// 						error: errors.created_after,
	// 						helperText: errors.created_after ? 'Некорректная дата' : '',
	// 					},
	// 				}}
	// 			/>
	// 		</div>
	// 	</div>
	// )
}

export default DateRangesPickerFilter
