'use client'

import { useState } from 'react'
import {
	Dialog,
	DialogContent,
	DialogTitle,
	useMediaQuery,
	useTheme,
	Button,
	DialogActions,
	Typography,
	Switch,
	TextField,
} from '@mui/material'
import styles from '@/app/nomenclatures/Nomenclatures.module.scss'
import ActionButton from '@/components/Ui/button/ActionButton'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import { useNomenclatureForm } from '@/app/nomenclatures/components/CreateNomenclature/hooks/useNomenclature'
import { DAY_KEYS } from '@/app/nomenclatures/components/CreateNomenclature/constans/constants'
import {
	BasicInfoFields,
	DaySettingsAccordion,
	DaySettingsGrid,
	CopyButton,
} from '@/app/nomenclatures/components/CreateNomenclature/components'
import { NomenclatureVolume } from '@/components/nomenclatures/NomenclatureVolume/NomenclatureVolume'

interface CreateNomenclatureProps {
	onSuccess?: () => void
}

export default function CreateNomenclature({ onSuccess }: CreateNomenclatureProps) {
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
		onSuccess?.()
	}

	return (
		<div>
			<ActionButton
				onClick={() => setOpen(true)}
				icon={AddCircleOutlineIcon}
				className='mt-5'
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
					className={styles.custom_scroll}
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
								<CopyButton
									onCopy={handleCopyMondaySettings}
									label='Применить настройки для всех дней'
									disabled={!formState.settings.mon.worktime}
								/>
								<TextField
									label='Рабочее время'
									fullWidth
									margin='dense'
									value={formState.settings.mon.worktime}
									onChange={handleDaySettingChange('mon', 'worktime')}
									error={!!formErrors['mon-worktime']}
									helperText={formErrors['mon-worktime'] || ''}
								/>
								<NomenclatureVolume
									value={formState.settings.mon.default_volume}
									onChange={(newVolume) => handleVolumeChange('mon', newVolume)}
									error={!!formErrors['mon-volume']}
									helperText={formErrors['mon-volume'] || ''}
								/>
							</div>
						) : (
							<div className='flex flex-row gap-4'>
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
											onWorktimeChange={handleDaySettingChange(day, 'worktime')}
											onVolumeChange={(newVolume) => handleVolumeChange(day, newVolume)}
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
