import { useState } from 'react'
import { Box, IconButton, Paper } from '@mui/material'
import FilterListIcon from '@mui/icons-material/FilterList'
import TextField from '@mui/material/TextField'
import Autocomplete from '@mui/material/Autocomplete'
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank'
import CheckBoxIcon from '@mui/icons-material/CheckBox'
import DateRangesPickerFilter from './DateRangesPickerFilter'
import { useStore } from '@/providers/mobx-provider/MobxProvider'
import Checkbox from '@mui/material/Checkbox'
import { Search } from '@/app/nomenclatures/components'
import { BrcTypeFilter } from './BrcTypeFilter'
import { OrderTypeFilter } from './OrderTypeFilter'

const FiltersPanel: React.FC = () => {
  const { ordersStore } = useStore()
  const activeTab = ordersStore.activeTab
  const [isFiltersPanelOpen, setIsFiltersPanelOpen] = useState(false)

  const handleFilterClick = () => {
    setIsFiltersPanelOpen((prev) => !prev)
  }

  return (
    <Box
      display={'flex'}
      height={'100%'}
      width={'100%'}
      justifyContent={'start'}
      alignItems={'center'}
    >
      <div className='flex flex-row items-center justify-center gap-4'>
        <DateRangesPickerFilter />
        <IconButton onClick={handleFilterClick}>
          <FilterListIcon />
        </IconButton>
      </div>
      {isFiltersPanelOpen && (
        <Box
          position={'absolute'}
          top={64}
          left={0}
          width={'100%'}
          boxSizing={'border-box'}
          padding={1}
          zIndex={1}
        >
          <Paper
            elevation={6}
            className='flex flex-row gap-1 w-full p-2 bg-gray-300 rounded-lg'
          >
            {/* Текстовые поля для имени и клиента */}
            <Search nameQueryParams='name' label='Название' />
            <Search nameQueryParams='client' label='Номенклатура' />
            {activeTab === 0 && <OrderTypeFilter />}
            {activeTab === 1 && <BrcTypeFilter />}
          </Paper>
        </Box>
      )}
    </Box>
  )
}

export default FiltersPanel
