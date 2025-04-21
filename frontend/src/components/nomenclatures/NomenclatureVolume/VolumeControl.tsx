import { Box, Grid, Slider, Typography, TextField } from '@mui/material'
import VolumeUpIcon from '@mui/icons-material/VolumeUp'
import { ChangeEvent } from 'react'

type VolumeControlProps = {
	index: number
	label: string
	volume: number
	color: string
	onSliderChange: (event: Event, newValue: number | number[]) => void
	onInputChange: (event: ChangeEvent<HTMLInputElement>) => void
	error?: boolean // Добавлен пропс error
	helperText?: string // Добавлен пропс helperText
}

export const VolumeControl = ({
	index,
	label,
	volume,
	color,
	onSliderChange,
	onInputChange,
	error, // Деструктуризация error
	helperText, // Деструктуризация helperText
}: VolumeControlProps) => (
	<Box
		textAlign='center'
		key={index}
	>
		<VolumeUpIcon />
		<Slider
			orientation='vertical'
			value={volume}
			onChange={onSliderChange}
			min={0}
			max={100}
			step={1}
			valueLabelDisplay='auto'
			sx={{ height: 120, mt: 1, color }}
			aria-label={`${label} громкость`}
		/>
		<TextField
			value={volume}
			onChange={onInputChange}
			size='small'
			type='number'
			inputProps={{ min: 0, max: 100 }}
			sx={{ width: 72, mt: 1 }}
			error={error} // Передача error в TextField
			helperText={helperText} // Передача helperText в TextField
		/>
		<Typography
			variant='body2'
			mt={0.5}
		>
			{label}
		</Typography>
	</Box>
)
