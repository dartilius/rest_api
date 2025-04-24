import { Accordion, AccordionSummary, AccordionDetails, Typography, TextField } from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import NomenclatureVolume from '@/components/nomenclatures/NomenclatureVolume/NomenclatureVolume'
import { ChangeEvent } from 'react'
import { DAY_LABELS } from '@/app/nomenclatures/components/CreateNomenclature/constans/constants'

export interface DaySettingsAccordionProps {
	day: string
	expanded: boolean
	onExpandChange: () => void
	settings: {
		worktime: string
		default_volume: [number, number, number, number]
	}
	errors: {
		worktime?: string
		volume?: string
	}
	onWorktimeChange: (e: ChangeEvent<HTMLInputElement>) => void
	onVolumeChange: (newVolume: [number, number, number, number]) => void
	handleWorktimeBlur?: (e: React.FocusEvent<HTMLInputElement>) => void
}

export const DaySettingsAccordion = ({
	day,
	expanded,
	onExpandChange,
	settings,
	errors,
	onWorktimeChange,
	onVolumeChange,
	handleWorktimeBlur,
}: DaySettingsAccordionProps) => (
	<div style={{ maxWidth: 320, width: '100%' }}>
		<Accordion
			expanded={expanded}
			onChange={onExpandChange}
		>
			<AccordionSummary expandIcon={<ExpandMoreIcon />}>
				<Typography>{DAY_LABELS[day]}</Typography>
			</AccordionSummary>
			<AccordionDetails>
				<div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
					<TextField
						label='Рабочее время'
						fullWidth
						margin='dense'
						value={settings.worktime}
						onChange={onWorktimeChange}
						onBlur={handleWorktimeBlur}
						error={!!errors.worktime}
						helperText={
							errors.worktime ||
							'Введите время в формате hh:mm-hh:mm или просто цифры (например: 10002100)'
						}
						placeholder='Например: 10002100 или 10:00-21:00'
					/>
					<NomenclatureVolume
						value={settings.default_volume}
						onChange={onVolumeChange}
						error={!!errors.volume}
						helperText={errors.volume || ''}
					/>
				</div>
			</AccordionDetails>
		</Accordion>
	</div>
)
