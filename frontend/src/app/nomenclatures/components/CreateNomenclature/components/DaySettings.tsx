import { Grid } from '@mui/material'
import ActionButton from '@/components/Ui/button/ActionButton'
import { ReactNode } from 'react'

export const CopyButton = ({ onCopy, label }: { onCopy: () => void; label: string }) => (
	<div>
		<ActionButton
			variant='warning'
			onClick={onCopy}
			className='mb-4'
		>
			{label}
		</ActionButton>
	</div>
)

export const DaySettingsGrid = ({ children }: { children: ReactNode }) => (
	<Grid
		container
		spacing={2}
		justifyContent='center'
	>
		{children}
	</Grid>
)
