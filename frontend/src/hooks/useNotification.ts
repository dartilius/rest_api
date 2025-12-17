'use client'

import { toast } from 'react-toastify'
import type { ToastOptions } from 'react-toastify'

export type NotificationType = 'success' | 'error' | 'info' | 'warning'

export const useNotification = () => {
  const showNotification = (
    text: string,
    type: NotificationType = 'success',
    options?: ToastOptions
  ) => {
    toast[type](text, {
      position: 'top-right',
      autoClose: 5000,
      hideProgressBar: false,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
      progress: undefined,
      ...options,
    })
  }

  return { showNotification }
}