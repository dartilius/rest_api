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
const DesktopViewDatePicker = ({
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
		<div className='flex flex-row w-full justify-end items-center gap-2'>
			<Label className='text-sm md:text-xl text-nowrap'>{label}</Label>
			<div className='w-full flex flex-row justify-end flex-nowrap gap-1'>
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
export default DesktopViewDatePicker
