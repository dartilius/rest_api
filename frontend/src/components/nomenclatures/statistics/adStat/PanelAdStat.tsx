import ActionButton from '@/components/Ui/button/ActionButton'
import { ThemeProvider } from '@emotion/react'
import { createTheme } from '@mui/material'
import { DatePicker } from '@mui/x-date-pickers'
import dayjs from 'dayjs'

const darkTheme = createTheme({
	palette: {
		mode: 'dark',
		primary: {
			main: '#fa5ff7',
		},
	},
	typography: {
		fontFamily: 'inherit',
	},
	components: {
		MuiPaper: {
			styleOverrides: {
				root: {
					background:
						'linear-gradient(to right, rgb(30, 58, 138), rgb(49, 46, 129), rgb(30, 64, 175))',
					'& .MuiPickersDay-root': {
						fontFamily: 'inherit',

						'&:hover': {
							backgroundColor: '#eb25e1',
						},
						'&.Mui-selected': {
							backgroundColor: '#fa5ff7',

							'&:hover': {
								backgroundColor: '#ad40ac',
							},
						},
					},
					'& .MuiPickersCalendarHeader-root': {
						color: 'white',
						fontFamily: 'inherit',

						'& .MuiPickersCalendarHeader-label': {},
					},
					'& .MuiDayCalendar-weekDayLabel': {
						color: 'rgba(255, 255, 255, 0.7)',
						fontFamily: 'inherit',
					},
					'& .MuiPickersDay-dayOutsideMonth': {
						color: 'rgba(255, 255, 255, 0.3)',
					},
				},
			},
		},
		MuiInputBase: {
			styleOverrides: {
				root: {
					fontFamily: 'inherit',
				},
			},
		},
	},
})

export default function PanelAdStat({
	setDate,
	date,
}: {
	setDate: (date: string) => void
	date: string
}) {
	return (
		<div className='sticky top-0 z-10'>
			<div className='flex items-center justify-between p-4 bg-blue-900 border-b border-blue-700'>
				<ActionButton
					className='bg-gradient-to-r from-blue-600 via-blue-500 to-blue-400 hover:from-blue-500 hover:via-blue-400 hover:to-blue-300'
					onClick={() => setDate('')}
				>
					Просмотреть всю статистику
				</ActionButton>

				<ThemeProvider theme={darkTheme}>
					<DatePicker
						value={dayjs(date)}
						onChange={(newValue) => newValue && setDate(newValue.format('YYYY-MM-DD'))}
						format='YYYY-MM-DD'
						slotProps={{
							textField: {
								size: 'small',
								sx: {
									'.MuiInputBase-root': {
										background:
											'linear-gradient(to right, rgb(30, 58, 138), rgb(49, 46, 129), rgb(30, 64, 175))',
										fontSize: '0.875rem',
									},
								},
							},
						}}
					/>
				</ThemeProvider>
			</div>
		</div>
	)
}
