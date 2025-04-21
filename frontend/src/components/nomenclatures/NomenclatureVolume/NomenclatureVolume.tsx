import { ChangeEvent } from 'react'
import { Box, Grid, Typography } from '@mui/material'
import { VolumeControl } from "@/components/nomenclatures/NomenclatureVolume/VolumeControl";

interface INomenclatureVolumeProps {
	value: [number, number, number, number]; // [Музыка Л, Реклама Л, Музыка П, Реклама П]
	onChange: (value: [number, number, number, number]) => void;
	error?: boolean; // Дополнительный пропс для ошибок
	helperText?: string; // Сообщение об ошибке или подсказка
}

export const NomenclatureVolume = ({ value, onChange, error, helperText }: INomenclatureVolumeProps) => {
	const handleSliderChange = (index: number) => (_: Event, newValue: number | number[]) => {
		const newVolume = [...value] as [number, number, number, number];
		newVolume[index] = newValue as number;
		onChange(newVolume);
	};

	const handleInputChange = (index: number) => (event: ChangeEvent<HTMLInputElement>) => {
		let newValue = parseInt(event.target.value, 10);
		if (isNaN(newValue)) newValue = 0;
		newValue = Math.min(100, Math.max(0, newValue));

		const newVolume = [...value] as [number, number, number, number];
		newVolume[index] = newValue;
		onChange(newVolume);
	};

	const controls = [
		{ index: 0, label: 'Музыка', color: '#163a67' }, // Левая Музыка
		{ index: 1, label: 'Реклама', color: '#163a67' }, // Левая Реклама
		{ index: 2, label: 'Музыка', color: '#f55f5f' }, // Правая Музыка
		{ index: 3, label: 'Реклама', color: '#f55f5f' }, // Правая Реклама
	];

	return (
		<Box
			display='flex'
			justifyContent='center'
			gap={6}
		>
			{/* Левая сторона */}
			<Box textAlign='center'>
				<Typography
					fontWeight='bold'
					mb={1}
				>
					Левая сторона
				</Typography>
				<Grid
					container
					spacing={2}
					justifyContent='center'
				>
					{controls.slice(0, 2).map(({ index, label, color }) => (
						<VolumeControl
							key={index}
							index={index}
							label={label}
							volume={value[index]}
							color={color}
							onSliderChange={handleSliderChange(index)}
							onInputChange={handleInputChange(index)}
							error={error} // Передаем error и helperText в VolumeControl
							helperText={helperText}
						/>
					))}
				</Grid>
			</Box>

			{/* Правая сторона */}
			<Box textAlign='center'>
				<Typography
					fontWeight='bold'
					mb={1}
				>
					Правая сторона
				</Typography>
				<Grid
					container
					spacing={2}
					justifyContent='center'
				>
					{controls.slice(2).map(({ index, label, color }) => (
						<VolumeControl
							key={index}
							index={index}
							label={label}
							volume={value[index]}
							color={color}
							onSliderChange={handleSliderChange(index)}
							onInputChange={handleInputChange(index)}
							error={error} // Передаем error и helperText в VolumeControl
							helperText={helperText}
						/>
					))}
				</Grid>
			</Box>
		</Box>
	);
}

export default NomenclatureVolume;
