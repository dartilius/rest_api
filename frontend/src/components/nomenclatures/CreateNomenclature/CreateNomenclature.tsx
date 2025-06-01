'use client'

import ActionButton from '@/components/Ui/button/ActionButton'
import { CopyButton } from '@/components/Ui/button/CoppyButton'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import {
	Box,
	Button,
	Dialog,
	DialogActions,
	DialogContent,
	DialogTitle,
	IconButton,
	Switch,
	TextField,
	Typography,
	useMediaQuery,
	useTheme,
} from '@mui/material'
import { useState } from 'react'
import { NomenclatureVolume } from '../NomenclatureVolume/NomenclatureVolume'
import { BasicInfoFields } from './components/BasicInfoFields'
import { DaySettingsGrid } from './components/DaySettings'
import { DaySettingsAccordion } from './components/DaySettingsAccordion'
import { DAY_KEYS } from './constans/constants'
import { useNomenclatureForm } from './hooks/useNomenclature'

export function CreateNomenclature() {
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
		<>
			{/* <Box
				display='flex'
				width='100%'
				height={'100%'}
				justifyContent='center'
				alignItems='center'
			> */}
				
				{isMobile ? (
					<ActionButton
						variant='primary'
						size='sm'
						icon={AddCircleOutlineIcon}
						onClick={() => setOpen(true)}
						className='h-full m-2'
					/>
				) : (
					<ActionButton
						variant='primary'
						size='lg'
						icon={AddCircleOutlineIcon}
						onClick={() => setOpen(true)}
					>
						Создать
					</ActionButton>
				)}
			{/* </Box> */}

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
		</>
	)
}
