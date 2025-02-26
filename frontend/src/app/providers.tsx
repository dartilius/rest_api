'use client'

import { AuthProvider } from '@/providers/auth/AuthProvider'
import { MobxProvider } from '@/providers/mobx-provider/MobxProvider'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AxiosError } from 'axios'
import { ReactNode } from 'react'

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
    <AuthProvider>
      <MobxProvider>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </MobxProvider>
    </AuthProvider>
  )
}

export default Providers
