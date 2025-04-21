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
} from '@mui/material'
import styles from '@/app/nomenclatures/Nomenclatures.module.scss'
import ActionButton from "@/components/Ui/button/ActionButton"
import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline"
import {useNomenclatureForm} from "@/app/nomenclatures/components/CreateNomenclature/hooks/useNomenclature";
import {
	DaySettingsGrid,
	DaySettingsHeader
} from "@/app/nomenclatures/components/CreateNomenclature/components/DaySettings";
import {DAY_KEYS} from "@/app/nomenclatures/components/CreateNomenclature/constans/constants";
import {DaySettingsAccordion} from "@/app/nomenclatures/components/CreateNomenclature/components/DaySettingsAccordion";
import BasicInfoFields from "@/app/nomenclatures/components/CreateNomenclature/components/BasicInfoFields";

interface CreateNomenclatureProps {
	onSuccess?: () => void
}

export default function CreateNomenclature({ onSuccess }: CreateNomenclatureProps) {
	const [open, setOpen] = useState(false)
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
		resetForm
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

				<DialogContent dividers className={styles.custom_scroll}>
					<BasicInfoFields
						formState={formState}
						handleTextChange={handleTextChange}
					/>

					<DaySettingsHeader
						onCopyMondaySettings={handleCopyMondaySettings}
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
									volume: formErrors[`${day}-volume`]
								}}
								onWorktimeChange={handleDaySettingChange(day, 'worktime')}
								onVolumeChange={(newVolume) => handleVolumeChange(day, newVolume)}
							/>
						))}
					</DaySettingsGrid>
				</DialogContent>

				<DialogActions>
					<Button onClick={handleClose} color='primary'>
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