import { AuthProvider } from '@/providers/auth/AuthProvider'
import { MobxProvider } from '@/providers/mobx-provider/MobxProvider'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AxiosError } from 'axios'
import 'dayjs/locale/ru'
import { ReactNode } from 'react'
import { NotificationProvider } from '@/providers/notification/NotificationProvider'
import { ThemeProvider } from '@mui/material'
import { theme } from '@/theme'

export interface ProvidersProps {
	children: ReactNode
}

const queryClient = new QueryClient({
	defaultOptions: {
		queries: {
			refetchOnWindowFocus: false,
			retry: (failureCount, error) => {
				const axiosError = error as AxiosError
				if (axiosError.response?.status === 401) {
					window.location.href = '/login'
					return false
				}
				return failureCount < 3
			},
		},
	},
})

function Providers({ children }: ProvidersProps) {
	return (
		<LocalizationProvider
			dateAdapter={AdapterDayjs}
			adapterLocale={'ru'}
		>
			<NotificationProvider>
				<AuthProvider>
					<MobxProvider>
						<QueryClientProvider client={queryClient}>
							<ThemeProvider theme={theme}>{children}</ThemeProvider>
						</QueryClientProvider>
					</MobxProvider>
				</AuthProvider>
			</NotificationProvider>
		</LocalizationProvider>
	)
}

export default Providers
