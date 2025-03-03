import { useState } from 'react'
import { Box, IconButton, Paper } from '@mui/material'
import FilterListIcon from '@mui/icons-material/FilterList'
import Checkbox from '@mui/material/Checkbox'
import TextField from '@mui/material/TextField'
import Autocomplete from '@mui/material/Autocomplete'
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank'
import CheckBoxIcon from '@mui/icons-material/CheckBox'
import DateRangesPickerFilter from './DateRangesPickerFilter'

type FilterOptions = {
  owner: string[]
  name: string[]
  order_type: string[]
  client: string[]
  created: string[]
}

const FILTER_OPTIONS: FilterOptions = {
  owner: ['Owner 1', 'Owner 2', 'Owner 3'],
  name: ['Name 1', 'Name 2', 'Name 3'],
  order_type: ['Type 1', 'Type 2', 'Type 3'],
  client: ['Client 1', 'Client 2', 'Client 3'],
  created: ['Today', 'Last 7 Days', 'Last 30 Days'],
}

const icon = <CheckBoxOutlineBlankIcon fontSize='small' />
const checkedIcon = <CheckBoxIcon fontSize='small' />

const FiltersPanel: React.FC = () => {
  const [isFiltersPanelOpen, setIsFiltersPanelOpen] = useState(false)

  const handleFilterClick = () => {
    setIsFiltersPanelOpen((prev) => !prev)
  }

  return (
    <Box
      display={'flex'}
      height={'100%'}
      justifyContent={'center'}
      alignItems={'center'}
    >
      <div className='flex flex-row items-center justify-center gap-2'>
        <IconButton onClick={handleFilterClick}>
          <FilterListIcon />
        </IconButton>
        <DateRangesPickerFilter />
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
            className='flex flex-row gap-1 w-full p-2  bg-gray-300 rounded-lg'
          >
            {Object.keys(FILTER_OPTIONS).map((filter) => (
              <Autocomplete
                fullWidth
                key={filter}
                multiple
                options={FILTER_OPTIONS[filter as keyof FilterOptions]}
                disableCloseOnSelect
                renderOption={(props, option, { selected }) => {
                  const { key, ...optionProps } = props
                  return (
                    <li key={key} {...optionProps}>
                      <Checkbox
                        icon={icon}
                        checkedIcon={checkedIcon}
                        style={{ marginRight: 8 }}
                        checked={selected}
                      />
                      {option}
                    </li>
                  )
                }}
                renderInput={(params) => (
                  <TextField {...params} label={filter} />
                )}
              />
            ))}
          </Paper>
        </Box>
      )}
    </Box>
  )
}

export default FiltersPanel
