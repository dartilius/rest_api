import { Grid } from '@mui/material'
import { ReactNode } from 'react'

export const DaySettingsGrid = ({ children }: { children: ReactNode }) => (
	<Grid
		container
		spacing={2}
		justifyContent='center'
	>
		{children}
	</Grid>
)
