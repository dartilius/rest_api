import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { Dayjs } from 'dayjs'
import { observer } from 'mobx-react'
import { useStore } from '@/providers/mobx-provider/MobxProvider'

const DateRangesPickerFilter = () => {
  const { ordersStore } = useStore()

  const handleStartDateChange = (newValue: Dayjs | null) => {
    ordersStore.setStartDate(newValue)
  }

  const handleEndDateChange = (newValue: Dayjs | null) => {
    ordersStore.setEndDate(newValue)
  }
  console.log('start', ordersStore.startDate)
  console.log('end', ordersStore.endDate)

  return (
    <div className='flex flex-row w-full justify-center items-center gap-2'>
      <DatePicker
        label='От'
        value={ordersStore.startDate}
        onChange={handleStartDateChange}
      />
      <DatePicker
        label='До'
        value={ordersStore.endDate}
        onChange={handleEndDateChange}
      />
    </div>
  )
}
export default observer(DateRangesPickerFilter)
