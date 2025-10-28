'use client'

import { ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import { ReactNode } from 'react'
import { Theme } from 'react-toastify'

export interface NotificationProviderProps {
  children: ReactNode
  theme?: Theme
}

export const NotificationProvider = ({ 
  children,
  theme = 'colored'
}: NotificationProviderProps) => {
  return (
    <>
      {children}
      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme={theme}
      />
    </>
  )
}