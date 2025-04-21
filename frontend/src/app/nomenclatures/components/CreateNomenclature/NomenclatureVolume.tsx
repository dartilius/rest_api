'use client'

import { Box, Grid, Slider, Typography, TextField } from '@mui/material'
import VolumeUpIcon from '@mui/icons-material/VolumeUp'
import {ChangeEvent} from "react";

type Props = {
    value: [number, number, number, number] // [Музыка Л, Реклама Л, Музыка П, Реклама П]
    onChange: (value: [number, number, number, number]) => void
}

export const NomenclatureVolume = ({ value, onChange }: Props) => {
    const handleSliderChange = (index: number) => (_: Event, newValue: number | number[]) => {
        const newVolume = [...value] as [number, number, number, number]
        newVolume[index] = newValue as number
        onChange(newVolume)
    }

    const handleInputChange = (index: number) => (event: ChangeEvent<HTMLInputElement>) => {
        let newValue = parseInt(event.target.value, 10)
        if (isNaN(newValue)) newValue = 0
        newValue = Math.min(100, Math.max(0, newValue))

        const newVolume = [...value] as [number, number, number, number]
        newVolume[index] = newValue
        onChange(newVolume)
    }

    return (
        <Box display="flex" justifyContent="center" gap={6}>
            {/* Левая сторона */}
            <Box textAlign="center">
                <Typography fontWeight="bold" mb={1}>
                    Левая сторона
                </Typography>
                <Grid container spacing={2} justifyContent="center">
                    {[0, 1].map((index) => (
                        <div key={index}>
                            <VolumeUpIcon />
                            <Slider
                                orientation="vertical"
                                value={value[index]}
                                onChange={handleSliderChange(index)}
                                min={0}
                                max={100}
                                step={1}
                                valueLabelDisplay="auto"
                                sx={{ height: 120, mt: 1 }}
                                style={{color: '#163a67'}}
                            />
                            <TextField
                                value={value[index]}
                                onChange={handleInputChange(index)}
                                size="small"
                                type="number"
                                inputProps={{ min: 0, max: 100 }}
                                sx={{ width: 64, mt: 1 }}
                            />
                            <Typography variant="body2" mt={0.5}>
                                {index === 0 ? 'Музыка' : 'Реклама'}
                            </Typography>
                        </div>
                    ))}
                </Grid>
            </Box>

            {/* Правая сторона */}
            <Box textAlign="center">
                <Typography fontWeight="bold" mb={1}>
                    Правая сторона
                </Typography>
                <Grid container spacing={2} justifyContent="center">
                    {[2, 3].map((index) => (
                        <div key={index}>
                            <VolumeUpIcon />
                            <Slider
                                orientation="vertical"
                                value={value[index]}
                                onChange={handleSliderChange(index)}
                                min={0}
                                max={100}
                                step={1}
                                valueLabelDisplay="auto"
                                sx={{ height: 120, mt: 1 }}
                                style={{color: '#f55f5f'}}
                            />
                            <TextField
                                value={value[index]}
                                onChange={handleInputChange(index)}
                                size="small"
                                type="number"
                                inputProps={{ min: 0, max: 100 }}
                                sx={{ width: 64, mt: 1 }}
                            />
                            <Typography variant="body2" mt={0.5}>
                                {index === 2 ? 'Музыка' : 'Реклама'}
                            </Typography>
                        </div>
                    ))}
                </Grid>
            </Box>
        </Box>
    )
}