'use client'
import { formatDateTime } from '@/utils/dateUtils'

interface DateTimeProps {
  date: string
  className?: string
}

export const DateTime = ({ date, className }: DateTimeProps) => {
  return (
    <span className={`font-mono ${className}`}>
      {formatDateTime(date)}
    </span>
  )
}