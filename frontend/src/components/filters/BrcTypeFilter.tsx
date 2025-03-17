// components/BrcTypeFilter.tsx
'use client'
import { useEffect, useState } from 'react'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import Autocomplete from '@mui/material/Autocomplete'
import TextField from '@mui/material/TextField'
import Checkbox from '@mui/material/Checkbox'
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank'
import CheckBoxIcon from '@mui/icons-material/CheckBox'
import { useStore } from '@/providers/mobx-provider/MobxProvider'
import { handleQueryParamChange } from '@/utils'

const icon = <CheckBoxOutlineBlankIcon fontSize='small' />
const checkedIcon = <CheckBoxIcon fontSize='small' />

const FILTER_OPTIONS = [
  { queryParams: '0', label: 'По времени работы точки' },
  { queryParams: '1', label: 'Начало работы + смещение по времени' },
  { queryParams: '2', label: 'Конец работы – смещение по времени' },
  { queryParams: '3', label: 'По конкретным часам' },
  { queryParams: '4', label: 'С открытия до конкретного часа' },
  { queryParams: '5', label: 'С фиксированного часа до закрытия' },
  { queryParams: '6', label: 'Старт по событию' },
]

export function BrcTypeFilter() {
  const { ordersStore } = useStore()
  const searchParams = useSearchParams()
  const pathname = usePathname()
  const router = useRouter()
  const currentValue = searchParams?.get('brc_type') || ''
  const [selectedValue, setSelectedValue] = useState<string>(currentValue)

  useEffect(() => {
    setSelectedValue(currentValue)
  }, [currentValue])

  const handleChange = (
    _: any,
    newValue: { queryParams: string; label: string } | null
  ) => {
    const value = newValue?.queryParams || ''
    setSelectedValue(value)
    handleQueryParamChange(router, pathname, searchParams, 'brc_type', value)
    ordersStore.setPage(1)
  }

  return (
    <Autocomplete
      fullWidth
      options={FILTER_OPTIONS}
      getOptionLabel={(option) => option.label}
      disableCloseOnSelect
      value={
        FILTER_OPTIONS.find((option) => option.queryParams === selectedValue) ||
        null
      }
      onChange={handleChange}
      renderOption={(props, option, { selected }) => {
        const { key, ...restProps } = props as {
          key: React.Key
        } & React.HTMLAttributes<HTMLLIElement>

        return (
          <li key={key} {...restProps}>
            <Checkbox
              icon={icon}
              checkedIcon={checkedIcon}
              style={{ marginRight: 8 }}
              checked={selected}
            />
            {option.label}
          </li>
        )
      }}
      renderInput={(params) => <TextField {...params} label='Тип вещания' />}
    />
  )
}
