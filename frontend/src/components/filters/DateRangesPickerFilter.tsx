'use client'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import dayjs, { Dayjs } from 'dayjs'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { handleQueryParamChange } from '@/utils'

const DATE_FORMAT = 'YYYY-MM-DD'
const DISPLAY_FORMAT = 'DD-MM-YYYY'

const DateRangesPickerFilter = () => {
  const searchParams = useSearchParams()
  const pathname = usePathname()
  const router = useRouter()

  const [createdAfter, setCreatedAfter] = useState<Dayjs | null>(null)
  const [createdBefore, setCreatedBefore] = useState<Dayjs | null>(null)
  const [errors, setErrors] = useState<Record<string, boolean>>({
    created_after: false,
    created_before: false
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

  const handleDateChange = (
    type: 'created_after' | 'created_before',
    date: Dayjs | null
  ) => {
    const isValid = isValidDate(date)
    setErrors(prev => ({ ...prev, [type]: !isValid }))

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

    handleQueryParamChange(
      router,
      pathname,
      searchParams,
      type,
      dateString
    )
  }

  return (
    <div className='flex flex-row w-full justify-center items-center gap-8'>
      <DatePicker
        label='От'
        value={createdAfter}
        onChange={(date) => handleDateChange('created_after', date)}
        format={DISPLAY_FORMAT}
        slotProps={{
          textField: {
            error: errors.created_after,
            helperText: errors.created_after ? 'Некорректная дата' : ''
          }
        }}
      />
      <DatePicker
        label='До'
        value={createdBefore}
        onChange={(date) => handleDateChange('created_before', date)}
        format={DISPLAY_FORMAT}
        slotProps={{
          textField: {
            error: errors.created_before,
            helperText: errors.created_before ? 'Некорректная дата' : ''
          }
        }}
      />
    </div>
  )
}

export default DateRangesPickerFilter