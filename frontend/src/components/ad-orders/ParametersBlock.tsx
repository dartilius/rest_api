import { AdOrderType } from '@/types/orderTypes'
import { Box, Typography, TextField, Button, MenuItem } from '@mui/material'
import { FormState } from './CreateAdOrderModal'

const ParametersBlock = ({
	type,
	parameters,
	onChange,
}: {
	type: AdOrderType
	parameters: FormState['parameters']
	onChange: (params: FormState['parameters']) => void
}) => {
	const handleChange = (field: keyof FormState['parameters']) => (value: any) => {
		onChange({ ...parameters, [field]: value })
	}

	return (
		<Box sx={{ border: '1px solid #eee', borderRadius: 1 }}>
			<Typography
				variant='h6'
				gutterBottom
			>
				Параметры вещания:
			</Typography>
			<Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
				<Box sx={{ flex: '1 1 33%', maxWidth: '33%' }}>
					<TextField
						label='Приоритет (0-100)'
						type='number'
						fullWidth
						margin='normal'
						value={parameters.weight}
						onChange={(e) => {
							const val = Math.min(Math.max(Number(e.target.value), 0), 100)
							handleChange('weight')(val)
						}}
						slotProps={{ htmlInput: { min: 0, max: 100 } }}
					/>
				</Box>

				<Box sx={{ flex: '1 1 66%', maxWidth: '66%', height: '100%' }}>
					<Typography
						variant='body2'
						sx={{ textAlign: 'center' }}
					>
						Количество выходов в час:
					</Typography>
					<Box
						sx={{
							display: 'flex',
							gap: 1,
							flexWrap: 'wrap',
							'& > button': {
								flex: '1 1 calc(16.666% - 8px)',
								minWidth: '60px',
								padding: '6px 8px',
							},
						}}
					>
						{[1, 2, 3, 4, 6, 12].map((num) => (
							<Button
								key={num}
								variant={parameters.times_in_hour === num ? 'contained' : 'outlined'}
								onClick={() => handleChange('times_in_hour')(num)}
							>
								{num}
							</Button>
						))}
					</Box>
				</Box>
			</Box>
			{[AdOrderType.START_OFFSET, AdOrderType.END_OFFSET].includes(type) && (
				<TextField
					select
					label='Смещение по времени'
					fullWidth
					margin='normal'
					value={parameters.timedelta || ''}
					onChange={(e) => handleChange('timedelta')(e.target.value)}
                   
				>
					{[5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55].map((minutes) => (
						<MenuItem sx={{
                        '&:hover': {
                            backgroundColor: 'rgba(141,202,246,0.3)',
                            cursor: 'pointer',
                        },
                        padding: '8px 16px',
                       
                    }}
							key={minutes}
							value={`00:${minutes.toString().padStart(2, '0')}:00`}
						>
							{minutes} минут
						</MenuItem>
					))}
				</TextField>
			)}

			{type === AdOrderType.SPECIFIC_HOURS && (
				<Box sx={{ display: 'flex', gap: 2 }}>
					<TextField
						label='Время начала'
						type='time'
						fullWidth
						margin='normal'
						slotProps={{ inputLabel: { shrink: true } }}
						value={parameters.start_time || ''}
						onChange={(e) => handleChange('start_time')(e.target.value)}
					/>
					<TextField
						label='Время окончания'
						type='time'
						fullWidth
						margin='normal'
						slotProps={{ inputLabel: { shrink: true } }}
						value={parameters.end_time || ''}
						onChange={(e) => handleChange('end_time')(e.target.value)}
					/>
				</Box>
			)}

			{type === AdOrderType.OPEN_TO_HOUR && (
				<TextField
					label='Время окончания'
					type='time'
					fullWidth
					margin='normal'
					slotProps={{ inputLabel: { shrink: true } }}
					value={parameters.end_time || ''}
					onChange={(e) => handleChange('end_time')(e.target.value)}
				/>
			)}

			{type === AdOrderType.FIXED_TO_CLOSE && (
				<TextField
					label='Время начала'
					type='time'
					fullWidth
					margin='normal'
					slotProps={{ inputLabel: { shrink: true } }}
					value={parameters.start_time || ''}
					onChange={(e) => handleChange('start_time')(e.target.value)}
				/>
			)}

			{type === AdOrderType.EVENT_START && (
				<>
					<TextField
						label='Событие'
						fullWidth
						margin='normal'
						value={parameters.event || ''}
						onChange={(e) => handleChange('event')(e.target.value)}
					/>
					<TextField
						label='Активная реклама'
						fullWidth
						margin='normal'
						value={parameters.active_ad || ''}
						onChange={(e) => handleChange('active_ad')(e.target.value)}
					/>
				</>
			)}
		</Box>
	)
}
export default ParametersBlock
