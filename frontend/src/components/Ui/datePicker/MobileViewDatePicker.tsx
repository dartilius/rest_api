import { Label } from '@/components/data-display/Label'
import { DatePicker } from '@mui/x-date-pickers'
import dayjs, { Dayjs } from 'dayjs'

interface IDataPickerProps {
  label: string
	valueFrom: dayjs.Dayjs | null
	valueTo: dayjs.Dayjs | null
	typeAfter: string
	typeBefore: string
	onChange: (type: string, date: Dayjs | null) => void
	formatDate: string
	errors: Record<string, boolean>
}
const MobileViewDatePicker = ({
  label,
	valueFrom,
	valueTo,
	typeAfter,
	typeBefore,
	onChange,
	formatDate,
	errors,
}: IDataPickerProps) => {
	return (
		<div className='flex flex-col w-full gap-2 p-1'>
			<Label className='text-sm md:text-2xl text-nowrap'>{label}</Label>

			<div className='flex flex-col gap-2'>
				<DatePicker
					label='От'
					value={valueFrom}
					onChange={(date) => onChange(typeAfter, date)}
					format={formatDate}
					slotProps={{
						textField: {
							size: 'small',
							fullWidth: true,
							error: errors.created_after,
							helperText: errors.created_after ? 'Некорректная дата' : '',
						},
					}}
				/>
				<DatePicker
					label='До'
					value={valueTo}
					onChange={(date) => onChange(typeBefore, date)}
					format={formatDate}
					slotProps={{
						textField: {
							size: 'small',
							fullWidth: true,
							error: errors.created_after,
							helperText: errors.created_after ? 'Некорректная дата' : '',
						},
					}}
				/>
			</div>
		</div>
	)
}
export default MobileViewDatePicker
