import { BgOrderType } from '@/types/orderTypes'
import { Box, Typography, TextField, Button } from '@mui/material'
import { FormStateBg } from './CreateBgOrderModal'

const ParametersBlockBg = ({
	// type,
	parameters,
	onChange,
}: {
	type: BgOrderType
	parameters: FormStateBg['parameters']
	onChange: (params: FormStateBg['parameters']) => void
}) => {
	const handleChange = (field: keyof FormStateBg['parameters']) => (value: any) => {
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
		</Box>
	)
}
export default ParametersBlockBg
