'use client'

import {
	BasicInfoFields,
	DaySettingsAccordion,
	DaySettingsGrid,
} from '@/app/nomenclatures/components/CreateNomenclature/components'
import { DAY_KEYS } from '@/app/nomenclatures/components/CreateNomenclature/constans/constants'
import { useNomenclatureForm } from '@/app/nomenclatures/components/CreateNomenclature/hooks/useNomenclature'
import { NomenclatureVolume } from '@/components/nomenclatures'
import ActionButton from '@/components/Ui/button/ActionButton'
import { CopyButton } from '@/components/Ui/button/CoppyButton'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import {
	Button,
	Dialog,
	DialogActions,
	DialogContent,
	DialogTitle,
	Switch,
	TextField,
	Typography,
	useMediaQuery,
	useTheme,
} from '@mui/material'
import { useState } from 'react'

export default function CreateNomenclature() {
	const [open, setOpen] = useState<boolean>(false)
	const [isDaySettings, setIsDaySettings] = useState<boolean>(false)
	const theme = useTheme()
	const isMobile = useMediaQuery(theme.breakpoints.down('sm'))

	const {
		formState,
		formErrors,
		expandedDay,
		handleTextChange,
		handleDaySettingChange,
		handleSubmit,
		handleCopyMondaySettings,
		handleVolumeChange,
		setExpandedDay,
		resetForm,
	} = useNomenclatureForm()

	const handleClose = () => {
		setOpen(false)
		resetForm()
	}

	const handleSuccess = () => {
		setOpen(false)
	}

	return (
		<div>
			<ActionButton
				onClick={() => setOpen(true)}
				icon={AddCircleOutlineIcon}
				style={{ maxHeight: '56px', height: '100%' }}
			>
				Создать номенклатуру
			</ActionButton>

			<Dialog
				open={open}
				onClose={handleClose}
				fullScreen={isMobile}
				maxWidth='md'
				fullWidth
			>
				<DialogTitle>Создание новой номенклатуры</DialogTitle>

				<DialogContent
					dividers
					className='custom_scroll'
				>
					<BasicInfoFields
						formState={formState}
						handleTextChange={handleTextChange}
					/>

					<Typography
						variant='h6'
						sx={{ mt: 2, mb: 1 }}
					>
						Настройки по дням недели
					</Typography>

					<div className='flex flex-col gap-4 items-center'>
						<div className='flex items-center gap-1'>
							<span>Общая настройка</span>
							<Switch
								checked={isDaySettings}
								onChange={() => setIsDaySettings(!isDaySettings)}
								color='secondary'
							/>

							<span>Настройка для каждого дня</span>
						</div>
						{!isDaySettings ? (
							<div className='flex flex-col gap-1 items-center'>
								<TextField
									label='Рабочее время'
									fullWidth
									margin='dense'
									value={formState.settings.mon.worktime}
									onChange={handleDaySettingChange('mon', 'worktime', isDaySettings)}
									error={!!formErrors['mon-worktime']}
									helperText={formErrors['mon-worktime'] || ''}
								/>
								<NomenclatureVolume
									value={formState.settings.mon.default_volume}
									onChange={(newVolume) => handleVolumeChange('mon', newVolume, isDaySettings)}
									error={!!formErrors['mon-volume']}
									helperText={formErrors['mon-volume'] || ''}
								/>
							</div>
						) : (
							<div className='flex flex-col gap-4 items-center'>
								<CopyButton
									onCopy={handleCopyMondaySettings}
									label='Применить настройки для всех дней'
									disabled={!formState.settings.mon.worktime}
								/>
								<DaySettingsGrid>
									{DAY_KEYS.map((day) => (
										<DaySettingsAccordion
											key={day}
											day={day}
											expanded={expandedDay === day}
											onExpandChange={() => setExpandedDay(expandedDay === day ? false : day)}
											settings={formState.settings[day]}
											errors={{
												worktime: formErrors[`${day}-worktime`],
												volume: formErrors[`${day}-volume`],
											}}
											onWorktimeChange={handleDaySettingChange(day, 'worktime', isDaySettings)}
											onVolumeChange={(newVolume) =>
												handleVolumeChange(day, newVolume, isDaySettings)
											}
										/>
									))}
								</DaySettingsGrid>
							</div>
						)}
					</div>
				</DialogContent>

				<DialogActions>
					<Button
						onClick={handleClose}
						color='primary'
					>
						Отмена
					</Button>
					<Button
						onClick={() => handleSubmit(handleSuccess)}
						color='primary'
						disabled={!formState.name}
					>
						Создать
					</Button>
				</DialogActions>
			</Dialog>
		</div>
	)
}
